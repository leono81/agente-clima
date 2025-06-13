"""
Server - Servidor FastAPI con HTTP + SSE + A2A
==============================================

Servidor FastAPI que proporciona acceso al agente del clima via:
- API REST estándar
- Server-Sent Events (SSE) para streaming
- Protocolo Agent-to-Agent (A2A)
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncGenerator

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sse_starlette import EventSourceResponse
from pydantic import BaseModel, Field
import uvicorn

from src.config.settings import get_settings
from src.config.apis import get_security_config, get_a2a_config
from src.core.agent import ClimaAgent, WeatherContext
from src.core.models import (
    WeatherResponse, Location, A2AMessage, A2ARequest, A2AResponse, 
    A2ATask, TaskStatus, ChatMessage, ChatSession
)
from src.interfaces.a2a_handler import A2AHandler
from src.utils.logging import (
    log_info, log_error, log_debug, log_agent_interaction,
    log_performance_metric, log_a2a_message, setup_auto_instrumentation
)


# Modelos de la API

class WeatherQuery(BaseModel):
    """Modelo para consultas meteorológicas."""
    location: str = Field(..., description="Ubicación para consultar")
    query_type: str = Field(default="current", description="Tipo de consulta")
    include_forecast: bool = Field(default=False, description="Incluir pronóstico")
    days: int = Field(default=7, ge=1, le=16, description="Días de pronóstico")


class ChatRequest(BaseModel):
    """Modelo para solicitudes de chat."""
    message: str = Field(..., description="Mensaje del usuario")
    session_id: Optional[str] = Field(None, description="ID de sesión")
    user_id: Optional[str] = Field(None, description="ID del usuario")
    stream: bool = Field(default=False, description="Respuesta en streaming")


class HealthCheck(BaseModel):
    """Modelo para health check."""
    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float


# Configuración de la aplicación

def create_app() -> FastAPI:
    """Crear la aplicación FastAPI."""
    
    settings = get_settings()
    security_config = get_security_config()
    
    app = FastAPI(
        title=settings.project_name,
        description=settings.description,
        version=settings.version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_config.cors_origins,
        allow_credentials=True,
        allow_methods=security_config.cors_methods,
        allow_headers=security_config.cors_headers,
    )
    
    # Instrumentar FastAPI con Logfire
    setup_auto_instrumentation(app)
    
    return app


# Crear aplicación
app = create_app()
security = HTTPBearer(auto_error=False)

# Variables globales
start_time = datetime.utcnow()
agent_instance = ClimaAgent()
a2a_handler = A2AHandler()
active_sessions: Dict[str, ChatSession] = {}


# Dependencias

async def get_current_agent() -> ClimaAgent:
    """Obtener instancia del agente."""
    return agent_instance


async def get_a2a_handler() -> A2AHandler:
    """Obtener handler A2A."""
    return a2a_handler


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """Verificar token de autorización (opcional)."""
    if not credentials:
        return None
    
    # Aquí puedes implementar validación de tokens JWT
    # Por ahora solo verificamos que existe
    return credentials.credentials


# Endpoints principales

@app.get("/")
async def root():
    """Página de inicio del servidor del agente del clima."""
    
    settings = get_settings()
    uptime = (datetime.utcnow() - start_time).total_seconds()
    
    return {
        "message": "🌤️ Servidor del Agente del Clima",
        "project": settings.project_name,
        "version": settings.version,
        "status": "running",
        "uptime_seconds": uptime,
        "endpoints": {
            "health": "/health",
            "status": "/status", 
            "docs": "/docs",
            "weather_current": "/api/weather/current",
            "weather_forecast": "/api/weather/forecast",
            "chat": "/api/chat",
            "a2a": "/api/a2a"
        },
        "examples": {
            "current_weather": "/api/weather/current",
            "forecast": "/api/weather/forecast", 
            "chat": "/api/chat",
            "health": "/health"
        }
    }


# Endpoints de Health Check

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check del servidor."""
    
    uptime = (datetime.utcnow() - start_time).total_seconds()
    settings = get_settings()
    
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.version,
        uptime_seconds=uptime
    )


@app.get("/status")
async def status_check(agent: ClimaAgent = Depends(get_current_agent)):
    """Estado detallado del agente."""
    
    try:
        agent_status = await agent.get_agent_status()
        settings = get_settings()
        uptime = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "server": {
                "status": "running",
                "uptime_seconds": uptime,
                "start_time": start_time.isoformat(),
                "host": settings.host,
                "port": settings.port
            },
            "agent": agent_status,
            "sessions": {
                "active_sessions": len(active_sessions),
                "total_messages": sum(len(session.messages) for session in active_sessions.values())
            }
        }
    
    except Exception as e:
        log_error(f"Error en status_check: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estado")


# Endpoints del Agente del Clima

@app.post("/api/weather/current")
async def get_current_weather(
    query: WeatherQuery,
    agent: ClimaAgent = Depends(get_current_agent),
    token: Optional[str] = Depends(verify_token)
):
    """Obtener clima actual para una ubicación."""
    
    log_info(f"Consulta clima actual: {query.location}")
    
    try:
        context = WeatherContext()
        user_query = f"¿Cómo está el clima actual en {query.location}?"
        
        response = await agent.process_query(user_query, context)
        
        return {
            "status": "success",
            "location": query.location,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
            "query_type": "current_weather"
        }
    
    except Exception as e:
        log_error(f"Error en get_current_weather: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo clima: {str(e)}")


# Función para ejecutar el servidor

def run_server():
    """Ejecutar el servidor FastAPI."""
    
    settings = get_settings()
    
    uvicorn.run(
        "src.interfaces.server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
        access_log=settings.debug
    )


if __name__ == "__main__":
    run_server()
