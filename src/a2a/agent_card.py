"""
Agent Card Generator - Generador de Tarjetas de Agente A2A
==========================================================

Genera Agent Cards según la especificación A2A para descubrimiento automático.
El Agent Card se expone en /.well-known/agent.json
"""

import json
from typing import Dict, Any
from datetime import datetime
from .models import AgentInfo, WeatherCapabilities


class AgentCardGenerator:
    """Generador de Agent Cards para descubrimiento A2A."""
    
    def __init__(self, agent_id: str, endpoint: str, port: int = 8001):
        self.agent_id = agent_id
        self.endpoint = endpoint
        self.port = port
    
    def generate_weather_agent_card(self) -> Dict[str, Any]:
        """Genera Agent Card para el agente de clima."""
        
        # Obtener capacidades del agente de clima
        capabilities = [
            WeatherCapabilities.get_current_weather_capability(),
            WeatherCapabilities.get_forecast_capability(),
            WeatherCapabilities.search_locations_capability()
        ]
        
        # Crear información del agente
        agent_info = AgentInfo(
            agent_id=self.agent_id,
            name="Weather Agent",
            description="Agente especializado en información meteorológica usando Open-Meteo API",
            version="1.0.0",
            capabilities=capabilities,
            endpoint=f"{self.endpoint}:{self.port}",
            status="active",
            metadata={
                "created_at": datetime.utcnow().isoformat(),
                "provider": "Open-Meteo",
                "supported_languages": ["es", "en"],
                "coverage": "global",
                "update_frequency": "real-time"
            }
        )
        
        # Generar Agent Card según especificación A2A
        agent_card = {
            "agent": {
                "id": agent_info.agent_id,
                "name": agent_info.name,
                "description": agent_info.description,
                "version": agent_info.version,
                "status": agent_info.status,
                "endpoint": agent_info.endpoint,
                "metadata": agent_info.metadata
            },
            "capabilities": [cap.dict() for cap in agent_info.capabilities],
            "communication": {
                "protocol": "JSON-RPC 2.0",
                "transport": "HTTP",
                "endpoints": {
                    "rpc": f"{self.endpoint}:{self.port}/rpc",
                    "health": f"{self.endpoint}:{self.port}/health",
                    "status": f"{self.endpoint}:{self.port}/status",
                    "tasks": f"{self.endpoint}:{self.port}/tasks"
                },
                "supported_methods": [
                    "get_current_weather",
                    "get_forecast", 
                    "search_locations",
                    "get_agent_info",
                    "get_capabilities",
                    "submit_task",
                    "get_task_status",
                    "cancel_task"
                ]
            },
            "discovery": {
                "well_known_path": "/.well-known/agent.json",
                "last_updated": datetime.utcnow().isoformat(),
                "ttl": 3600  # 1 hora
            },
            "authentication": {
                "required": False,
                "methods": ["none"],
                "note": "Autenticación opcional para uso futuro"
            },
            "rate_limiting": {
                "requests_per_minute": 60,
                "burst_limit": 10
            },
            "examples": {
                "get_current_weather": {
                    "request": {
                        "jsonrpc": "2.0",
                        "method": "get_current_weather",
                        "params": {"location": "Buenos Aires"},
                        "id": "1"
                    },
                    "response": {
                        "jsonrpc": "2.0",
                        "result": {
                            "location": {"name": "Buenos Aires", "country": "Argentina"},
                            "current_weather": {
                                "temperature": 22.5,
                                "condition": "Soleado",
                                "humidity": 65
                            },
                            "status": "success"
                        },
                        "id": "1"
                    }
                }
            }
        }
        
        return agent_card
    
    def save_agent_card(self, filepath: str = "static/.well-known/agent.json") -> None:
        """Guarda el Agent Card en el archivo especificado."""
        
        agent_card = self.generate_weather_agent_card()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(agent_card, f, indent=2, ensure_ascii=False)
    
    def get_agent_card_json(self) -> str:
        """Retorna el Agent Card como JSON string."""
        
        agent_card = self.generate_weather_agent_card()
        return json.dumps(agent_card, indent=2, ensure_ascii=False)


def create_weather_agent_card(
    agent_id: str = "weather-agent-001",
    endpoint: str = "http://localhost",
    port: int = 8001
) -> Dict[str, Any]:
    """Función helper para crear Agent Card del agente de clima."""
    
    generator = AgentCardGenerator(agent_id, endpoint, port)
    return generator.generate_weather_agent_card()


def save_weather_agent_card(
    agent_id: str = "weather-agent-001",
    endpoint: str = "http://localhost", 
    port: int = 8001,
    filepath: str = "static/.well-known/agent.json"
) -> None:
    """Función helper para guardar Agent Card del agente de clima."""
    
    generator = AgentCardGenerator(agent_id, endpoint, port)
    generator.save_agent_card(filepath) 