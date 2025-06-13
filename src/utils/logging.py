"""
Logging - Sistema de Logs con Pydantic Logfire
==============================================

Sistema de logging robusto usando Pydantic Logfire para observabilidad
completa del agente, incluyendo trazas de PydanticAI y MCP.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from functools import wraps

import logfire
from logfire import configure, info, warning, error, debug, span, instrument
from src.config.settings import get_settings


class LoggingManager:
    """Manager centralizado del sistema de logging."""
    
    def __init__(self):
        self.settings = get_settings()
        self.configured = False
        self._setup_logging()
    
    def _setup_logging(self):
        """Configurar Pydantic Logfire y logging estándar."""
        try:
            # Configurar Logfire si está disponible el token
            if self.settings.logfire_token:
                logfire.configure(
                    token=self.settings.logfire_token,
                    service_name=self.settings.project_name,
                    service_version=self.settings.version,
                    environment="development" if self.settings.debug else "production"
                )
                self.configured = True
                logfire.info("Logfire configurado correctamente")
            else:
                # Configurar Logfire en modo local (sin token)
                logfire.configure(
                    send_to_logfire=False,  # No enviar datos externos
                    console=True,  # Mostrar en consola
                    service_name=self.settings.project_name,
                    service_version=self.settings.version
                )
                self.configured = True
                logfire.info("Logfire configurado en modo local")
                
        except Exception as e:
            print(f"Error configurando Logfire: {e}")
            self._setup_fallback_logging()
    
    def _setup_fallback_logging(self):
        """Configurar logging estándar como fallback."""
        log_level = logging.DEBUG if self.settings.debug else logging.INFO
        
        # Configurar logging a archivo
        log_file = self.settings.logs_dir / "clima_agent.log"
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        print(f"Logging estándar configurado: {log_file}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """Obtener logger con el nombre especificado."""
        return logging.getLogger(name)


# Instancia global del manager
_logging_manager = LoggingManager()


# Funciones de conveniencia para logging
def log_info(message: str, **kwargs):
    """Log de información."""
    logfire.info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """Log de advertencia."""
    logfire.warning(message, **kwargs)


def log_error(message: str, **kwargs):
    """Log de error."""
    logfire.error(message, **kwargs)


def log_debug(message: str, **kwargs):
    """Log de debug."""
    logfire.debug(message, **kwargs)


# Decoradores para instrumentación
def log_function_call(func_name: Optional[str] = None):
    """Decorador para loggear llamadas a funciones."""
    def decorator(func):
        name = func_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with logfire.span(f"function_call: {name}"):
                logfire.info(f"Iniciando {name}", args=len(args), kwargs=list(kwargs.keys()))
                try:
                    result = await func(*args, **kwargs)
                    logfire.info(f"Completado {name}")
                    return result
                except Exception as e:
                    logfire.error(f"Error en {name}: {str(e)}")
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with logfire.span(f"function_call: {name}"):
                logfire.info(f"Iniciando {name}", args=len(args), kwargs=list(kwargs.keys()))
                try:
                    result = func(*args, **kwargs)
                    logfire.info(f"Completado {name}")
                    return result
                except Exception as e:
                    logfire.error(f"Error en {name}: {str(e)}")
                    raise
        
        # Retornar wrapper apropiado
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_agent_interaction(operation: str):
    """Decorador específico para interacciones del agente."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with logfire.span(f"agent_interaction: {operation}"):
                logfire.info(f"Agente: {operation}", operation=operation)
                try:
                    result = await func(*args, **kwargs)
                    logfire.info(f"Agente completó: {operation}")
                    return result
                except Exception as e:
                    logfire.error(f"Error en agente: {operation} - {str(e)}")
                    raise
        
        return wrapper
    return decorator


def log_mcp_call(tool_name: str):
    """Decorador para llamadas MCP."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with logfire.span(f"mcp_call: {tool_name}"):
                logfire.info(f"MCP Tool: {tool_name}", tool=tool_name)
                try:
                    result = await func(*args, **kwargs)
                    logfire.info(f"MCP Tool completado: {tool_name}")
                    return result
                except Exception as e:
                    logfire.error(f"Error en MCP Tool: {tool_name} - {str(e)}")
                    raise
        
        return wrapper
    return decorator


def log_a2a_message(message_type: str):
    """Decorador para mensajes A2A."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with logfire.span(f"a2a_message: {message_type}"):
                logfire.info(f"A2A: {message_type}", message_type=message_type)
                try:
                    result = await func(*args, **kwargs)
                    logfire.info(f"A2A completado: {message_type}")
                    return result
                except Exception as e:
                    logfire.error(f"Error en A2A: {message_type} - {str(e)}")
                    raise
        
        return wrapper
    return decorator


# Context managers para operaciones complejas
class WeatherOperationSpan:
    """Context manager para operaciones meteorológicas."""
    
    def __init__(self, operation: str, location: Optional[str] = None):
        self.operation = operation
        self.location = location
        self.span = None
    
    def __enter__(self):
        self.span = logfire.span(f"weather_operation: {self.operation}")
        self.span.__enter__()
        logfire.info(
            f"Operación meteorológica: {self.operation}",
            operation=self.operation,
            location=self.location
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logfire.error(
                f"Error en operación meteorológica: {self.operation} - {str(exc_val)}",
                operation=self.operation,
                location=self.location
            )
        else:
            logfire.info(
                f"Operación meteorológica completada: {self.operation}",
                operation=self.operation,
                location=self.location
            )
        
        self.span.__exit__(exc_type, exc_val, exc_tb)


# Instrumentación automática para bibliotecas externas
def setup_auto_instrumentation(app=None):
    """Configurar instrumentación automática."""
    try:
        # Instrumentar httpx para llamadas HTTP
        logfire.instrument_httpx()
        
        # Instrumentar OpenAI
        logfire.instrument_openai()
        
        # Instrumentar FastAPI solo si se proporciona la app
        if app is not None:
            logfire.instrument_fastapi(app)
        
        logfire.info("Instrumentación automática configurada")
        
    except Exception as e:
        logfire.warning(f"Error configurando instrumentación automática: {e}")


# Inicializar instrumentación básica (sin FastAPI)
setup_auto_instrumentation()


def get_logger(name: str) -> logging.Logger:
    """Obtener logger estándar."""
    return _logging_manager.get_logger(name)


# Funciones de utilidad para logging estructurado
def log_weather_request(location: str, request_type: str, **metadata):
    """Log estructurado para solicitudes meteorológicas."""
    logfire.info(
        "Solicitud meteorológica",
        location=location,
        request_type=request_type,
        **metadata
    )


def log_weather_response(location: str, status: str, **metadata):
    """Log estructurado para respuestas meteorológicas."""
    logfire.info(
        "Respuesta meteorológica",
        location=location,
        status=status,
        **metadata
    )


def log_agent_decision(decision: str, reasoning: str, confidence: float):
    """Log estructurado para decisiones del agente."""
    logfire.info(
        "Decisión del agente",
        decision=decision,
        reasoning=reasoning,
        confidence=confidence
    )


def log_performance_metric(operation: str, duration_ms: float, **metadata):
    """Log de métricas de performance."""
    logfire.info(
        "Métrica de performance",
        operation=operation,
        duration_ms=duration_ms,
        **metadata
    ) 