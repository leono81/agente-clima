"""
A2A Server - Servidor Agent2Agent
=================================

Servidor FastAPI que implementa el protocolo A2A con JSON-RPC 2.0.
Maneja comunicación entre agentes, descubrimiento y gestión de tareas.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from .models import (
    A2ARequest, A2AResponse, A2ATask, TaskStatus, A2AError,
    WeatherCapabilities
)
from .agent_card import AgentCardGenerator
from ..core.weather_mcp import WeatherService
from ..utils.logging import log_info, log_error


class A2AServer:
    """Servidor A2A para comunicación entre agentes."""
    
    def __init__(self, agent_id: str = "weather-agent-001", port: int = 8001):
        self.agent_id = agent_id
        self.port = port
        self.tasks: Dict[str, A2ATask] = {}
        self.weather_service = WeatherService()
        self.app = None
        
        # Generar Agent Card
        self.agent_card_generator = AgentCardGenerator(
            agent_id=agent_id,
            endpoint="http://localhost",
            port=port
        )
    
    def create_app(self) -> FastAPI:
        """Crear aplicación FastAPI."""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            log_info(f"Iniciando servidor A2A en puerto {self.port}")
            self.agent_card_generator.save_agent_card()
            log_info("Agent Card generado y guardado")
            yield
            # Shutdown
            log_info("Cerrando servidor A2A")
        
        app = FastAPI(
            title="Weather Agent A2A Server",
            description="Servidor A2A para agente meteorológico",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # Montar archivos estáticos para Agent Card
        app.mount("/static", StaticFiles(directory="static"), name="static")
        
        # Endpoints A2A
        self._setup_routes(app)
        
        return app
    
    def _setup_routes(self, app: FastAPI):
        """Configurar rutas del servidor A2A."""
        
        @app.get("/.well-known/agent.json")
        async def get_agent_card():
            """Endpoint de descubrimiento A2A."""
            try:
                agent_card = self.agent_card_generator.generate_weather_agent_card()
                return JSONResponse(content=agent_card)
            except Exception as e:
                log_error(f"Error generando Agent Card: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @app.get("/health")
        async def health_check():
            """Endpoint de salud del agente."""
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "active_tasks": len(self.tasks)
            }
        
        @app.get("/status")
        async def get_status():
            """Endpoint de estado del agente."""
            return {
                "agent_id": self.agent_id,
                "status": "active",
                "capabilities": [
                    "get_current_weather",
                    "get_forecast", 
                    "search_locations"
                ],
                "active_tasks": len(self.tasks),
                "uptime": datetime.utcnow().isoformat()
            }
        
        @app.get("/tasks")
        async def get_tasks():
            """Obtener lista de tareas."""
            return {
                "tasks": [task.dict() for task in self.tasks.values()],
                "count": len(self.tasks)
            }
        
        @app.get("/tasks/{task_id}")
        async def get_task(task_id: str):
            """Obtener estado de una tarea específica."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Tarea no encontrada")
            
            return self.tasks[task_id].dict()
        
        @app.post("/rpc")
        async def handle_rpc(request: Request):
            """Endpoint principal JSON-RPC 2.0."""
            try:
                body = await request.json()
                log_info(f"Solicitud RPC recibida: {body.get('method', 'unknown')}")
                
                # Validar formato JSON-RPC 2.0
                if not self._validate_jsonrpc_request(body):
                    return self._create_error_response(
                        None, -32600, "Solicitud inválida"
                    )
                
                # Procesar solicitud
                response = await self._process_rpc_request(body)
                return JSONResponse(content=response)
                
            except json.JSONDecodeError:
                return self._create_error_response(
                    None, -32700, "Error de parsing JSON"
                )
            except Exception as e:
                log_error(f"Error procesando RPC: {e}")
                return self._create_error_response(
                    None, -32603, "Error interno del servidor"
                )
    
    def _validate_jsonrpc_request(self, body: Dict[str, Any]) -> bool:
        """Validar formato JSON-RPC 2.0."""
        return (
            isinstance(body, dict) and
            body.get("jsonrpc") == "2.0" and
            "method" in body and
            isinstance(body["method"], str)
        )
    
    async def _process_rpc_request(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar solicitud JSON-RPC 2.0."""
        method = body["method"]
        params = body.get("params", {})
        request_id = body.get("id")
        
        try:
            # Métodos de gestión de agente
            if method == "get_agent_info":
                result = await self._get_agent_info()
            elif method == "get_capabilities":
                result = await self._get_capabilities()
            elif method == "submit_task":
                result = await self._submit_task(params)
            elif method == "get_task_status":
                result = await self._get_task_status(params)
            elif method == "cancel_task":
                result = await self._cancel_task(params)
            
            # Métodos de clima (ejecución directa)
            elif method == "get_current_weather":
                result = await self._get_current_weather(params)
            elif method == "get_forecast":
                result = await self._get_forecast(params)
            elif method == "search_locations":
                result = await self._search_locations(params)
            
            else:
                return self._create_error_response(
                    request_id, -32601, f"Método no encontrado: {method}"
                )
            
            return self._create_success_response(request_id, result)
            
        except Exception as e:
            log_error(f"Error ejecutando método {method}: {e}")
            return self._create_error_response(
                request_id, -32603, f"Error ejecutando {method}: {str(e)}"
            )
    
    async def _get_agent_info(self) -> Dict[str, Any]:
        """Obtener información del agente."""
        agent_card = self.agent_card_generator.generate_weather_agent_card()
        return agent_card["agent"]
    
    async def _get_capabilities(self) -> List[Dict[str, Any]]:
        """Obtener capacidades del agente."""
        capabilities = [
            WeatherCapabilities.get_current_weather_capability(),
            WeatherCapabilities.get_forecast_capability(),
            WeatherCapabilities.search_locations_capability()
        ]
        return [cap.dict() for cap in capabilities]
    
    async def _submit_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enviar tarea para ejecución asíncrona."""
        capability = params.get("capability")
        input_data = params.get("input_data", {})
        
        if not capability:
            raise ValueError("Capacidad requerida")
        
        # Crear tarea
        task = A2ATask(
            agent_id=self.agent_id,
            capability=capability,
            input_data=input_data,
            status=TaskStatus.SUBMITTED
        )
        
        self.tasks[task.task_id] = task
        
        # Ejecutar tarea en background
        asyncio.create_task(self._execute_task(task.task_id))
        
        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "created_at": task.created_at.isoformat()
        }
    
    async def _get_task_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener estado de una tarea."""
        task_id = params.get("task_id")
        
        if not task_id or task_id not in self.tasks:
            raise ValueError("Tarea no encontrada")
        
        # Convertir datetime a string para serialización JSON
        task_dict = self.tasks[task_id].dict()
        task_dict["created_at"] = task_dict["created_at"].isoformat()
        task_dict["updated_at"] = task_dict["updated_at"].isoformat()
        
        return task_dict
    
    async def _cancel_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cancelar una tarea."""
        task_id = params.get("task_id")
        
        if not task_id or task_id not in self.tasks:
            raise ValueError("Tarea no encontrada")
        
        task = self.tasks[task_id]
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            raise ValueError("No se puede cancelar tarea completada")
        
        task.status = TaskStatus.CANCELLED
        task.updated_at = datetime.utcnow()
        
        return {"task_id": task_id, "status": "cancelled"}
    
    async def _execute_task(self, task_id: str):
        """Ejecutar tarea en background."""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = TaskStatus.WORKING
        task.updated_at = datetime.utcnow()
        
        try:
            # Ejecutar según capacidad
            if task.capability == "get_current_weather":
                result = await self._get_current_weather(task.input_data)
            elif task.capability == "get_forecast":
                result = await self._get_forecast(task.input_data)
            elif task.capability == "search_locations":
                result = await self._search_locations(task.input_data)
            else:
                raise ValueError(f"Capacidad no soportada: {task.capability}")
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            log_error(f"Error ejecutando tarea {task_id}: {e}")
        
        task.updated_at = datetime.utcnow()
    
    def _serialize_datetime_fields(self, data: Any) -> Any:
        """Convertir recursivamente todos los campos datetime a string."""
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {key: self._serialize_datetime_fields(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._serialize_datetime_fields(item) for item in data]
        else:
            return data

    async def _get_current_weather(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener clima actual."""
        location = params.get("location")
        if not location:
            raise ValueError("Ubicación requerida")
        
        # Crear nueva instancia del servicio para evitar problemas de conexión
        weather_service = WeatherService()
        weather_response = await weather_service.get_weather_by_location(location)
        
        if weather_response.status == "error":
            raise ValueError(weather_response.error_message)
        
        # Convertir todos los datetime a string para serialización JSON
        response_dict = weather_response.dict()
        return self._serialize_datetime_fields(response_dict)
    
    async def _get_forecast(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener pronóstico meteorológico."""
        location = params.get("location")
        days = params.get("days", 7)
        
        if not location:
            raise ValueError("Ubicación requerida")
        
        # Implementar lógica de pronóstico
        # Por ahora retornamos estructura básica
        return {
            "location": {"name": location},
            "forecast": {"days": days, "data": []},
            "status": "success"
        }
    
    async def _search_locations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Buscar ubicaciones."""
        query = params.get("query")
        limit = params.get("limit", 5)
        
        if not query:
            raise ValueError("Query requerido")
        
        # Crear nueva instancia del servicio para evitar problemas de conexión
        weather_service = WeatherService()
        async with weather_service.mcp_client:
            locations = await weather_service.mcp_client.search_location(query, limit)
        
        return {
            "locations": [loc.dict() for loc in locations],
            "count": len(locations),
            "status": "success"
        }
    
    def _create_success_response(self, request_id: Union[str, int, None], result: Any) -> Dict[str, Any]:
        """Crear respuesta exitosa JSON-RPC 2.0."""
        response = {
            "jsonrpc": "2.0",
            "result": result
        }
        
        if request_id is not None:
            response["id"] = request_id
        
        return response
    
    def _create_error_response(
        self, 
        request_id: Union[str, int, None], 
        code: int, 
        message: str, 
        data: Any = None
    ) -> Dict[str, Any]:
        """Crear respuesta de error JSON-RPC 2.0."""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        
        response = {
            "jsonrpc": "2.0",
            "error": error
        }
        
        if request_id is not None:
            response["id"] = request_id
        
        return response
    
    def run(self, host: str = "0.0.0.0", debug: bool = False):
        """Ejecutar servidor A2A."""
        if not self.app:
            self.app = self.create_app()
        
        uvicorn.run(
            self.app,
            host=host,
            port=self.port,
            log_level="info" if not debug else "debug"
        )


def create_a2a_server(agent_id: str = "weather-agent-001", port: int = 8001) -> A2AServer:
    """Factory function para crear servidor A2A."""
    return A2AServer(agent_id=agent_id, port=port) 