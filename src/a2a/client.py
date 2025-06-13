"""
A2A Client - Cliente Agent2Agent
================================

Cliente para comunicación con otros agentes A2A.
Incluye descubrimiento automático, envío de tareas y gestión de respuestas.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import httpx
from urllib.parse import urljoin

from .models import (
    A2ARequest, A2AResponse, A2ATask, TaskStatus, A2AError,
    AgentInfo, A2ACapability
)
from ..utils.logging import log_info, log_error


class A2AClient:
    """Cliente A2A para comunicación con otros agentes."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.discovered_agents: Dict[str, AgentInfo] = {}
        self.http_client = httpx.AsyncClient(timeout=timeout)
    
    async def __aenter__(self):
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.http_client.aclose()
    
    async def discover_agent(self, endpoint: str) -> Optional[AgentInfo]:
        """Descubrir un agente en un endpoint específico."""
        try:
            log_info(f"Descubriendo agente en {endpoint}")
            
            # Construir URL del Agent Card
            agent_card_url = urljoin(endpoint, "/.well-known/agent.json")
            
            # Obtener Agent Card
            response = await self.http_client.get(agent_card_url)
            response.raise_for_status()
            
            agent_card = response.json()
            
            # Extraer información del agente
            agent_data = agent_card.get("agent", {})
            capabilities_data = agent_card.get("capabilities", [])
            
            # Crear objetos de capacidades
            capabilities = []
            for cap_data in capabilities_data:
                capability = A2ACapability(**cap_data)
                capabilities.append(capability)
            
            # Crear información del agente
            agent_info = AgentInfo(
                agent_id=agent_data["id"],
                name=agent_data["name"],
                description=agent_data["description"],
                version=agent_data["version"],
                capabilities=capabilities,
                endpoint=endpoint,
                status=agent_data.get("status", "unknown"),
                metadata=agent_data.get("metadata", {})
            )
            
            # Guardar agente descubierto
            self.discovered_agents[agent_info.agent_id] = agent_info
            
            log_info(f"Agente descubierto: {agent_info.name} ({agent_info.agent_id})")
            log_info(f"Capacidades: {[cap.name for cap in agent_info.capabilities]}")
            
            return agent_info
            
        except httpx.HTTPStatusError as e:
            log_error(f"Error HTTP descubriendo agente en {endpoint}: {e.response.status_code}")
            return None
        except Exception as e:
            log_error(f"Error descubriendo agente en {endpoint}: {e}")
            return None
    
    async def discover_agents(self, endpoints: List[str]) -> List[AgentInfo]:
        """Descubrir múltiples agentes en paralelo."""
        log_info(f"Descubriendo {len(endpoints)} agentes...")
        
        tasks = [self.discover_agent(endpoint) for endpoint in endpoints]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        discovered = []
        for result in results:
            if isinstance(result, AgentInfo):
                discovered.append(result)
        
        log_info(f"Descubiertos {len(discovered)} agentes exitosamente")
        return discovered
    
    async def send_rpc_request(
        self, 
        endpoint: str, 
        method: str, 
        params: Optional[Dict[str, Any]] = None,
        request_id: Optional[Union[str, int]] = None
    ) -> Dict[str, Any]:
        """Enviar solicitud JSON-RPC 2.0 a un agente."""
        
        if request_id is None:
            request_id = f"req-{datetime.utcnow().timestamp()}"
        
        # Construir solicitud JSON-RPC 2.0
        rpc_request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id
        }
        
        if params:
            rpc_request["params"] = params
        
        try:
            log_info(f"Enviando RPC {method} a {endpoint}")
            
            # Construir URL del endpoint RPC
            rpc_url = urljoin(endpoint, "/rpc")
            
            # Enviar solicitud
            response = await self.http_client.post(
                rpc_url,
                json=rpc_request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # Procesar respuesta
            rpc_response = response.json()
            
            # Validar formato JSON-RPC 2.0
            if not self._validate_jsonrpc_response(rpc_response):
                raise ValueError("Respuesta JSON-RPC inválida")
            
            log_info(f"RPC {method} completado exitosamente")
            return rpc_response
            
        except httpx.HTTPStatusError as e:
            log_error(f"Error HTTP en RPC {method}: {e.response.status_code}")
            raise
        except Exception as e:
            log_error(f"Error en RPC {method}: {e}")
            raise
    
    def _validate_jsonrpc_response(self, response: Dict[str, Any]) -> bool:
        """Validar formato de respuesta JSON-RPC 2.0."""
        return (
            isinstance(response, dict) and
            response.get("jsonrpc") == "2.0" and
            ("result" in response or "error" in response) and
            "id" in response
        )
    
    async def get_agent_capabilities(self, endpoint: str) -> List[A2ACapability]:
        """Obtener capacidades de un agente."""
        try:
            response = await self.send_rpc_request(endpoint, "get_capabilities")
            
            if "result" in response:
                capabilities_data = response["result"]
                capabilities = []
                for cap_data in capabilities_data:
                    capability = A2ACapability(**cap_data)
                    capabilities.append(capability)
                return capabilities
            else:
                log_error(f"Error obteniendo capacidades: {response.get('error', {})}")
                return []
                
        except Exception as e:
            log_error(f"Error obteniendo capacidades de {endpoint}: {e}")
            return []
    
    async def get_agent_info(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Obtener información de un agente."""
        try:
            response = await self.send_rpc_request(endpoint, "get_agent_info")
            
            if "result" in response:
                return response["result"]
            else:
                log_error(f"Error obteniendo info del agente: {response.get('error', {})}")
                return None
                
        except Exception as e:
            log_error(f"Error obteniendo info de {endpoint}: {e}")
            return None
    
    async def submit_task(
        self, 
        endpoint: str, 
        capability: str, 
        input_data: Dict[str, Any]
    ) -> Optional[str]:
        """Enviar tarea a un agente para ejecución asíncrona."""
        try:
            params = {
                "capability": capability,
                "input_data": input_data
            }
            
            response = await self.send_rpc_request(endpoint, "submit_task", params)
            
            if "result" in response:
                task_info = response["result"]
                task_id = task_info.get("task_id")
                log_info(f"Tarea enviada: {task_id} ({capability})")
                return task_id
            else:
                log_error(f"Error enviando tarea: {response.get('error', {})}")
                return None
                
        except Exception as e:
            log_error(f"Error enviando tarea a {endpoint}: {e}")
            return None
    
    async def get_task_status(self, endpoint: str, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de una tarea."""
        try:
            params = {"task_id": task_id}
            response = await self.send_rpc_request(endpoint, "get_task_status", params)
            
            if "result" in response:
                return response["result"]
            else:
                log_error(f"Error obteniendo estado de tarea: {response.get('error', {})}")
                return None
                
        except Exception as e:
            log_error(f"Error obteniendo estado de tarea {task_id}: {e}")
            return None
    
    async def wait_for_task_completion(
        self, 
        endpoint: str, 
        task_id: str, 
        max_wait: int = 60,
        poll_interval: int = 2
    ) -> Optional[Dict[str, Any]]:
        """Esperar a que una tarea se complete."""
        log_info(f"Esperando completación de tarea {task_id}...")
        
        start_time = datetime.utcnow()
        
        while True:
            # Verificar timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > max_wait:
                log_error(f"Timeout esperando tarea {task_id}")
                return None
            
            # Obtener estado de la tarea
            task_status = await self.get_task_status(endpoint, task_id)
            if not task_status:
                return None
            
            status = task_status.get("status")
            
            if status == TaskStatus.COMPLETED.value:
                log_info(f"Tarea {task_id} completada exitosamente")
                return task_status
            elif status == TaskStatus.FAILED.value:
                log_error(f"Tarea {task_id} falló: {task_status.get('error', 'Error desconocido')}")
                return task_status
            elif status == TaskStatus.CANCELLED.value:
                log_info(f"Tarea {task_id} fue cancelada")
                return task_status
            
            # Esperar antes del siguiente poll
            await asyncio.sleep(poll_interval)
    
    async def execute_capability_sync(
        self, 
        endpoint: str, 
        capability: str, 
        input_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Ejecutar capacidad de manera síncrona (llamada directa)."""
        try:
            response = await self.send_rpc_request(endpoint, capability, input_data)
            
            if "result" in response:
                log_info(f"Capacidad {capability} ejecutada exitosamente")
                return response["result"]
            else:
                log_error(f"Error ejecutando {capability}: {response.get('error', {})}")
                return None
                
        except Exception as e:
            log_error(f"Error ejecutando {capability} en {endpoint}: {e}")
            return None
    
    async def execute_capability_async(
        self, 
        endpoint: str, 
        capability: str, 
        input_data: Dict[str, Any],
        max_wait: int = 60
    ) -> Optional[Dict[str, Any]]:
        """Ejecutar capacidad de manera asíncrona (via tareas)."""
        # Enviar tarea
        task_id = await self.submit_task(endpoint, capability, input_data)
        if not task_id:
            return None
        
        # Esperar completación
        task_result = await self.wait_for_task_completion(endpoint, task_id, max_wait)
        if not task_result:
            return None
        
        # Retornar resultado
        if task_result.get("status") == TaskStatus.COMPLETED.value:
            return task_result.get("result")
        else:
            return None
    
    def get_discovered_agents(self) -> List[AgentInfo]:
        """Obtener lista de agentes descubiertos."""
        return list(self.discovered_agents.values())
    
    def get_agent_by_id(self, agent_id: str) -> Optional[AgentInfo]:
        """Obtener agente por ID."""
        return self.discovered_agents.get(agent_id)
    
    def get_agents_with_capability(self, capability_name: str) -> List[AgentInfo]:
        """Obtener agentes que tienen una capacidad específica."""
        agents = []
        for agent in self.discovered_agents.values():
            for capability in agent.capabilities:
                if capability.name == capability_name:
                    agents.append(agent)
                    break
        return agents


class WeatherAgentClient:
    """Cliente especializado para comunicarse con agentes de clima."""
    
    def __init__(self, timeout: int = 30):
        self.client = A2AClient(timeout=timeout)
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def discover_weather_agents(self, endpoints: List[str]) -> List[AgentInfo]:
        """Descubrir agentes de clima."""
        agents = await self.client.discover_agents(endpoints)
        
        # Filtrar solo agentes con capacidades meteorológicas
        weather_agents = []
        for agent in agents:
            has_weather_capability = any(
                cap.name in ["get_current_weather", "get_forecast", "search_locations"]
                for cap in agent.capabilities
            )
            if has_weather_capability:
                weather_agents.append(agent)
        
        return weather_agents
    
    async def get_current_weather(self, endpoint: str, location: str) -> Optional[Dict[str, Any]]:
        """Obtener clima actual de un agente de clima."""
        input_data = {"location": location}
        return await self.client.execute_capability_sync(
            endpoint, "get_current_weather", input_data
        )
    
    async def get_forecast(
        self, 
        endpoint: str, 
        location: str, 
        days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """Obtener pronóstico de un agente de clima."""
        input_data = {"location": location, "days": days}
        return await self.client.execute_capability_sync(
            endpoint, "get_forecast", input_data
        )
    
    async def search_locations(
        self, 
        endpoint: str, 
        query: str, 
        limit: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Buscar ubicaciones en un agente de clima."""
        input_data = {"query": query, "limit": limit}
        return await self.client.execute_capability_sync(
            endpoint, "search_locations", input_data
        )


# Factory functions
def create_a2a_client(timeout: int = 30) -> A2AClient:
    """Factory function para crear cliente A2A."""
    return A2AClient(timeout=timeout)


def create_weather_agent_client(timeout: int = 30) -> WeatherAgentClient:
    """Factory function para crear cliente de agente de clima."""
    return WeatherAgentClient(timeout=timeout) 