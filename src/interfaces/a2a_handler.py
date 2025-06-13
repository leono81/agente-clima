"""
A2A Handler - Protocolo Agent-to-Agent
======================================

Implementación del protocolo Agent-to-Agent (A2A) de Google para
comunicación entre agentes de IA.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.config.settings import get_settings
from src.config.apis import get_a2a_config
from src.core.models import (
    A2AMessage, A2ARequest, A2AResponse, A2ATask, TaskStatus,
    AgentConfig
)
from src.utils.logging import (
    log_a2a_message, log_info, log_error, log_debug
)


class A2AHandler:
    """Handler para el protocolo Agent-to-Agent."""
    
    def __init__(self):
        self.settings = get_settings()
        self.a2a_config = get_a2a_config()
        self.tasks: Dict[str, A2ATask] = {}
        self.agent_config = self._create_agent_config()
        self.initialized = False
    
    def _create_agent_config(self) -> AgentConfig:
        """Crear configuración del agente."""
        
        return AgentConfig(
            agent_id=self.a2a_config.supported_task_types[0] if self.a2a_config.supported_task_types else "clima-agent",
            name=self.settings.project_name,
            version=self.settings.version,
            description=self.settings.description,
            capabilities=[
                "weather_current",
                "weather_forecast",
                "location_search",
                "weather_recommendations"
            ],
            supported_languages=["es", "en"],
            max_concurrent_requests=10,
            timeout_seconds=self.a2a_config.task_timeout,
            rate_limit=100
        )
    
    async def initialize(self):
        """Inicializar el handler A2A."""
        
        if self.initialized:
            return
        
        log_info("Inicializando A2A Handler")
        
        try:
            # Configurar limpieza automática de tareas
            asyncio.create_task(self._cleanup_expired_tasks())
            
            self.initialized = True
            log_info("A2A Handler inicializado correctamente")
            
        except Exception as e:
            log_error(f"Error inicializando A2A Handler: {e}")
            raise
    
    async def cleanup(self):
        """Limpiar recursos del handler."""
        
        log_info("Limpiando A2A Handler")
        
        # Cancelar tareas pendientes
        for task in self.tasks.values():
            if task.status in [TaskStatus.SUBMITTED, TaskStatus.WORKING]:
                task.status = TaskStatus.FAILED
                task.error = "Servidor cerrándose"
                task.updated_at = datetime.utcnow()
        
        self.initialized = False
        log_info("A2A Handler limpiado")
    
    async def get_discovery_info(self) -> Dict[str, Any]:
        """Obtener información de descubrimiento del agente."""
        
        return {
            "agent": self.agent_config.dict(),
            "protocol": {
                "version": self.a2a_config.protocol_version,
                "message_format": self.a2a_config.message_format,
                "supported_transports": ["http", "sse"],
                "endpoints": {
                    "discovery": self.a2a_config.discovery_endpoint,
                    "tasks": self.a2a_config.tasks_endpoint,
                    "status": self.a2a_config.status_endpoint
                }
            },
            "capabilities": {
                "task_types": self.a2a_config.supported_task_types,
                "max_concurrent": self.agent_config.max_concurrent_requests,
                "timeout_seconds": self.agent_config.timeout_seconds,
                "rate_limit": self.agent_config.rate_limit
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @log_a2a_message("create_task")
    async def create_task(self, request: A2ARequest) -> A2ATask:
        """Crear nueva tarea A2A."""
        
        # Validar tipo de tarea
        if request.task_type not in self.a2a_config.supported_task_types:
            raise ValueError(f"Tipo de tarea no soportado: {request.task_type}")
        
        # Crear tarea
        task = A2ATask(
            task_id=str(uuid.uuid4()),
            agent_id=request.agent_id,
            task_type=request.task_type,
            status=TaskStatus.SUBMITTED,
            payload=request.params or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Almacenar tarea
        self.tasks[task.task_id] = task
        
        log_info(f"Tarea A2A creada: {task.task_id} ({task.task_type})")
        return task
    
    async def get_task(self, task_id: str) -> Optional[A2ATask]:
        """Obtener tarea por ID."""
        
        return self.tasks.get(task_id)
    
    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Actualizar estado de una tarea."""
        
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = status
        task.updated_at = datetime.utcnow()
        
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
        
        log_debug(f"Tarea {task_id} actualizada a estado: {status}")
        return True
    
    async def complete_task(self, task_id: str, result: Any) -> bool:
        """Completar tarea con resultado."""
        
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        log_info(f"Tarea A2A completada: {task_id}")
        return True
    
    async def fail_task(self, task_id: str, error: str) -> bool:
        """Marcar tarea como fallida."""
        
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = TaskStatus.FAILED
        task.error = error
        task.updated_at = datetime.utcnow()
        
        log_error(f"Tarea A2A fallida: {task_id} - {error}")
        return True
    
    async def get_tasks_by_status(self, status: TaskStatus) -> List[A2ATask]:
        """Obtener tareas por estado."""
        
        return [task for task in self.tasks.values() if task.status == status]
    
    async def get_tasks_by_agent(self, agent_id: str) -> List[A2ATask]:
        """Obtener tareas de un agente específico."""
        
        return [task for task in self.tasks.values() if task.agent_id == agent_id]
    
    async def process_message(self, message: A2AMessage) -> A2AResponse:
        """Procesar mensaje A2A entrante."""
        
        try:
            method = message.method
            params = message.params or {}
            
            if method == "agent.discover":
                result = await self.get_discovery_info()
            
            elif method == "task.create":
                # Crear solicitud A2A desde el mensaje
                request = A2ARequest(
                    id=message.id,
                    agent_id=params.get("agent_id", "unknown"),
                    task_type=params.get("task_type", ""),
                    **params
                )
                
                task = await self.create_task(request)
                result = {
                    "task_id": task.task_id,
                    "status": task.status,
                    "created_at": task.created_at.isoformat()
                }
            
            elif method == "task.status":
                task_id = params.get("task_id")
                if not task_id:
                    raise ValueError("task_id requerido")
                
                task = await self.get_task(task_id)
                if not task:
                    raise ValueError("Tarea no encontrada")
                
                result = task.dict()
            
            elif method == "agent.status":
                result = {
                    "agent": self.agent_config.dict(),
                    "tasks": {
                        "total": len(self.tasks),
                        "submitted": len(await self.get_tasks_by_status(TaskStatus.SUBMITTED)),
                        "working": len(await self.get_tasks_by_status(TaskStatus.WORKING)),
                        "completed": len(await self.get_tasks_by_status(TaskStatus.COMPLETED)),
                        "failed": len(await self.get_tasks_by_status(TaskStatus.FAILED))
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            else:
                raise ValueError(f"Método no soportado: {method}")
            
            return A2AResponse(
                id=message.id,
                result=result
            )
        
        except Exception as e:
            log_error(f"Error procesando mensaje A2A: {e}")
            return A2AResponse(
                id=message.id,
                error={
                    "code": -32603,
                    "message": "Error interno del servidor",
                    "data": str(e)
                }
            )
    
    async def send_message(self, target_agent: str, message: A2AMessage) -> A2AResponse:
        """Enviar mensaje a otro agente (placeholder)."""
        
        # Esta función sería implementada para enviar mensajes a otros agentes
        # Por ahora es un placeholder
        
        log_info(f"Enviando mensaje A2A a {target_agent}: {message.method}")
        
        # Simular respuesta
        return A2AResponse(
            id=message.id,
            result={"status": "message_sent", "target": target_agent}
        )
    
    async def _cleanup_expired_tasks(self):
        """Limpiar tareas expiradas periódicamente."""
        
        while self.initialized:
            try:
                current_time = datetime.utcnow()
                expired_tasks = []
                
                for task_id, task in self.tasks.items():
                    # Tareas que llevan más de 1 hora sin actualizar
                    if (current_time - task.updated_at).total_seconds() > 3600:
                        if task.status in [TaskStatus.SUBMITTED, TaskStatus.WORKING]:
                            expired_tasks.append(task_id)
                
                # Marcar tareas expiradas como fallidas
                for task_id in expired_tasks:
                    await self.fail_task(task_id, "Tarea expirada por timeout")
                
                # Eliminar tareas completadas/fallidas muy antiguas (más de 24 horas)
                old_tasks = []
                for task_id, task in self.tasks.items():
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                        if (current_time - task.updated_at).total_seconds() > 86400:  # 24 horas
                            old_tasks.append(task_id)
                
                for task_id in old_tasks:
                    del self.tasks[task_id]
                
                if expired_tasks or old_tasks:
                    log_info(f"Limpieza A2A: {len(expired_tasks)} expiradas, {len(old_tasks)} eliminadas")
                
                # Esperar 5 minutos antes de la próxima limpieza
                await asyncio.sleep(300)
                
            except Exception as e:
                log_error(f"Error en limpieza de tareas A2A: {e}")
                await asyncio.sleep(60)  # Esperar 1 minuto en caso de error
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del handler A2A."""
        
        total_tasks = len(self.tasks)
        status_counts = {}
        
        for status in TaskStatus:
            status_counts[status.value] = len([
                task for task in self.tasks.values() 
                if task.status == status
            ])
        
        return {
            "total_tasks": total_tasks,
            "status_distribution": status_counts,
            "agent_config": self.agent_config.dict(),
            "initialized": self.initialized,
            "supported_task_types": self.a2a_config.supported_task_types
        } 