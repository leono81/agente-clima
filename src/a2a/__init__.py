"""
A2A (Agent2Agent) Module
========================

Implementación del protocolo Agent2Agent para comunicación entre agentes.
Basado en JSON-RPC 2.0 con descubrimiento automático y gestión de tareas.
"""

from .models import *
from .agent_card import *
from .server import *
from .client import *

__version__ = "1.0.0"
__all__ = [
    "A2ATask", "A2AMessage", "A2ACapability", "AgentCard",
    "A2AServer", "A2AClient", "TaskStatus"
] 