"""
A2A Models - Modelos para Agent2Agent Protocol
==============================================

Modelos Pydantic para el protocolo A2A basado en JSON-RPC 2.0.
Incluye gestión de tareas, capacidades y mensajes entre agentes.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    """Estados de las tareas A2A."""
    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class A2ACapability(BaseModel):
    """Capacidad de un agente A2A."""
    
    name: str = Field(..., description="Nombre de la capacidad")
    description: str = Field(..., description="Descripción de la capacidad")
    input_schema: Dict[str, Any] = Field(..., description="Schema de entrada")
    output_schema: Dict[str, Any] = Field(..., description="Schema de salida")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Ejemplos de uso")


class A2ATask(BaseModel):
    """Tarea A2A."""
    
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único de la tarea")
    agent_id: str = Field(..., description="ID del agente que ejecuta la tarea")
    capability: str = Field(..., description="Capacidad solicitada")
    input_data: Dict[str, Any] = Field(..., description="Datos de entrada")
    status: TaskStatus = Field(default=TaskStatus.SUBMITTED, description="Estado de la tarea")
    result: Optional[Dict[str, Any]] = Field(None, description="Resultado de la tarea")
    error: Optional[str] = Field(None, description="Error si la tarea falló")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de creación")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Última actualización")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")


class A2AMessage(BaseModel):
    """Mensaje A2A basado en JSON-RPC 2.0."""
    
    jsonrpc: str = Field(default="2.0", description="Versión JSON-RPC")
    id: Optional[Union[str, int]] = Field(None, description="ID del mensaje")
    method: Optional[str] = Field(None, description="Método a ejecutar")
    params: Optional[Dict[str, Any]] = Field(None, description="Parámetros del método")
    result: Optional[Any] = Field(None, description="Resultado de la operación")
    error: Optional[Dict[str, Any]] = Field(None, description="Error de la operación")


class A2ARequest(A2AMessage):
    """Solicitud A2A."""
    
    method: str = Field(..., description="Método requerido")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parámetros")
    id: Union[str, int] = Field(default_factory=lambda: str(uuid.uuid4()), description="ID de solicitud")


class A2AResponse(A2AMessage):
    """Respuesta A2A."""
    
    id: Union[str, int] = Field(..., description="ID de la solicitud original")


class A2AError(BaseModel):
    """Error A2A."""
    
    code: int = Field(..., description="Código de error")
    message: str = Field(..., description="Mensaje de error")
    data: Optional[Any] = Field(None, description="Datos adicionales del error")


class AgentInfo(BaseModel):
    """Información básica de un agente."""
    
    agent_id: str = Field(..., description="ID único del agente")
    name: str = Field(..., description="Nombre del agente")
    description: str = Field(..., description="Descripción del agente")
    version: str = Field(..., description="Versión del agente")
    capabilities: List[A2ACapability] = Field(..., description="Capacidades del agente")
    endpoint: str = Field(..., description="Endpoint del agente")
    status: str = Field(default="active", description="Estado del agente")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")


class WeatherCapabilities:
    """Definición de capacidades específicas del agente de clima."""
    
    @staticmethod
    def get_current_weather_capability() -> A2ACapability:
        """Capacidad para obtener clima actual."""
        return A2ACapability(
            name="get_current_weather",
            description="Obtiene el clima actual para una ubicación específica",
            input_schema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Nombre de la ubicación (ciudad, país)"
                    }
                },
                "required": ["location"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "object"},
                    "current_weather": {"type": "object"},
                    "status": {"type": "string"},
                    "generated_at": {"type": "string"}
                }
            },
            examples=[
                {
                    "input": {"location": "Buenos Aires"},
                    "output": {
                        "location": {"name": "Buenos Aires", "country": "Argentina"},
                        "current_weather": {
                            "temperature": 22.5,
                            "condition": "Soleado",
                            "humidity": 65
                        },
                        "status": "success"
                    }
                }
            ]
        )
    
    @staticmethod
    def get_forecast_capability() -> A2ACapability:
        """Capacidad para obtener pronóstico."""
        return A2ACapability(
            name="get_forecast",
            description="Obtiene el pronóstico meteorológico para una ubicación",
            input_schema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Nombre de la ubicación"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Número de días (1-16)",
                        "minimum": 1,
                        "maximum": 16,
                        "default": 7
                    }
                },
                "required": ["location"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "object"},
                    "forecast": {"type": "object"},
                    "status": {"type": "string"}
                }
            },
            examples=[
                {
                    "input": {"location": "Madrid", "days": 3},
                    "output": {
                        "location": {"name": "Madrid", "country": "España"},
                        "forecast": {"daily_data": []},
                        "status": "success"
                    }
                }
            ]
        )
    
    @staticmethod
    def search_locations_capability() -> A2ACapability:
        """Capacidad para buscar ubicaciones."""
        return A2ACapability(
            name="search_locations",
            description="Busca ubicaciones por nombre",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Término de búsqueda"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Límite de resultados",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "locations": {"type": "array"},
                    "count": {"type": "integer"},
                    "status": {"type": "string"}
                }
            },
            examples=[
                {
                    "input": {"query": "Paris", "limit": 3},
                    "output": {
                        "locations": [
                            {"name": "Paris", "country": "France"},
                            {"name": "Paris", "country": "United States"}
                        ],
                        "count": 2,
                        "status": "success"
                    }
                }
            ]
        ) 