#!/usr/bin/env python3
"""
Production Configuration for A2A Weather Agent
==============================================

Configuración optimizada para entorno de producción:
- Variables de entorno
- Logging estructurado
- Monitoreo y métricas
- Seguridad
- Escalabilidad
"""

import os
import logging
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class ProductionConfig:
    """Configuración de producción."""
    
    # Servidor
    host: str = "0.0.0.0"
    port: int = 8001
    workers: int = 4
    max_connections: int = 1000
    keepalive_timeout: int = 65
    
    # Seguridad
    enable_cors: bool = True
    cors_origins: list = None
    api_key_required: bool = False
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 100
    
    # Cache y Performance
    cache_enabled: bool = True
    cache_size: int = 10000
    cache_ttl_default: int = 300
    connection_pool_size: int = 100
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    enable_access_logs: bool = True
    
    # Monitoreo
    metrics_enabled: bool = True
    health_check_interval: int = 30
    prometheus_enabled: bool = False
    prometheus_port: int = 9090
    
    # Base de datos (para métricas y cache persistente)
    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379"
    postgres_enabled: bool = False
    postgres_url: str = "postgresql://user:pass@localhost/weatherdb"
    
    # APIs externas
    weather_api_timeout: int = 30
    weather_api_retries: int = 3
    weather_api_backoff: float = 1.0
    
    # Alertas
    alerts_enabled: bool = False
    alert_webhook_url: Optional[str] = None
    alert_email: Optional[str] = None
    
    def __post_init__(self):
        """Validar y procesar configuración."""
        if self.cors_origins is None:
            self.cors_origins = ["*"] if not self.api_key_required else []
        
        # Cargar desde variables de entorno
        self._load_from_env()
    
    def _load_from_env(self):
        """Cargar configuración desde variables de entorno."""
        env_mappings = {
            "WEATHER_AGENT_HOST": "host",
            "WEATHER_AGENT_PORT": ("port", int),
            "WEATHER_AGENT_WORKERS": ("workers", int),
            "WEATHER_AGENT_LOG_LEVEL": "log_level",
            "WEATHER_AGENT_API_KEY_REQUIRED": ("api_key_required", bool),
            "WEATHER_AGENT_RATE_LIMIT": ("max_requests_per_minute", int),
            "WEATHER_AGENT_CACHE_SIZE": ("cache_size", int),
            "WEATHER_AGENT_REDIS_URL": "redis_url",
            "WEATHER_AGENT_POSTGRES_URL": "postgres_url",
            "WEATHER_AGENT_ALERT_WEBHOOK": "alert_webhook_url",
            "WEATHER_AGENT_ALERT_EMAIL": "alert_email",
        }
        
        for env_var, config_attr in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                if isinstance(config_attr, tuple):
                    attr_name, attr_type = config_attr
                    if attr_type == bool:
                        setattr(self, attr_name, env_value.lower() in ('true', '1', 'yes'))
                    else:
                        setattr(self, attr_name, attr_type(env_value))
                else:
                    setattr(self, config_attr, env_value)


class ProductionLogger:
    """Logger estructurado para producción."""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self._setup_logging()
    
    def _setup_logging(self):
        """Configurar logging estructurado."""
        
        # Configurar nivel de logging
        log_level = getattr(logging, self.config.log_level.upper())
        
        # Crear formatter
        if self.config.log_format == "json":
            formatter = self._create_json_formatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Configurar handlers
        handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
        
        # File handler si está configurado
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        
        # Configurar logging root
        logging.basicConfig(
            level=log_level,
            handlers=handlers,
            force=True
        )
        
        # Configurar loggers específicos
        self._configure_specific_loggers()
    
    def _create_json_formatter(self):
        """Crear formatter JSON."""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # Agregar información adicional si existe
                if hasattr(record, 'request_id'):
                    log_entry["request_id"] = record.request_id
                
                if hasattr(record, 'agent_id'):
                    log_entry["agent_id"] = record.agent_id
                
                if hasattr(record, 'method'):
                    log_entry["method"] = record.method
                
                if hasattr(record, 'latency'):
                    log_entry["latency"] = record.latency
                
                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)
                
                return json.dumps(log_entry)
        
        return JSONFormatter()
    
    def _configure_specific_loggers(self):
        """Configurar loggers específicos."""
        # Reducir verbosidad de librerías externas
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(
            logging.INFO if self.config.enable_access_logs else logging.WARNING
        )


class ProductionMonitoring:
    """Sistema de monitoreo para producción."""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self.metrics: Dict[str, Any] = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "response_times": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "circuit_breaker_trips": 0,
            "rate_limit_rejections": 0
        }
        self.alerts_sent = set()
    
    def record_request(self, method: str, success: bool, latency: float):
        """Registrar solicitud."""
        self.metrics["requests_total"] += 1
        
        if success:
            self.metrics["requests_successful"] += 1
        else:
            self.metrics["requests_failed"] += 1
        
        self.metrics["response_times"].append(latency)
        
        # Mantener solo las últimas 1000 mediciones
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
        
        # Verificar alertas
        self._check_alerts()
    
    def record_cache_hit(self):
        """Registrar cache hit."""
        self.metrics["cache_hits"] += 1
    
    def record_cache_miss(self):
        """Registrar cache miss."""
        self.metrics["cache_misses"] += 1
    
    def record_circuit_breaker_trip(self):
        """Registrar circuit breaker trip."""
        self.metrics["circuit_breaker_trips"] += 1
    
    def record_rate_limit_rejection(self):
        """Registrar rate limit rejection."""
        self.metrics["rate_limit_rejections"] += 1
    
    def get_health_status(self) -> Dict[str, Any]:
        """Obtener estado de salud."""
        total_requests = self.metrics["requests_total"]
        
        if total_requests == 0:
            success_rate = 1.0
            avg_latency = 0.0
        else:
            success_rate = self.metrics["requests_successful"] / total_requests
            avg_latency = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
        
        cache_total = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = self.metrics["cache_hits"] / max(1, cache_total)
        
        # Determinar estado de salud
        health_status = "healthy"
        
        if success_rate < 0.95:  # Menos del 95% de éxito
            health_status = "degraded"
        
        if success_rate < 0.8 or avg_latency > 5.0:  # Menos del 80% o latencia > 5s
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "metrics": {
                "requests_total": total_requests,
                "success_rate": f"{success_rate:.3f}",
                "average_latency": f"{avg_latency:.3f}s",
                "cache_hit_rate": f"{cache_hit_rate:.3f}",
                "circuit_breaker_trips": self.metrics["circuit_breaker_trips"],
                "rate_limit_rejections": self.metrics["rate_limit_rejections"]
            },
            "timestamp": self._get_timestamp()
        }
    
    def _check_alerts(self):
        """Verificar y enviar alertas."""
        if not self.config.alerts_enabled:
            return
        
        health = self.get_health_status()
        
        # Alerta por estado degradado
        if health["status"] == "degraded" and "degraded" not in self.alerts_sent:
            self._send_alert("Service Degraded", health)
            self.alerts_sent.add("degraded")
        
        # Alerta por estado no saludable
        if health["status"] == "unhealthy" and "unhealthy" not in self.alerts_sent:
            self._send_alert("Service Unhealthy", health)
            self.alerts_sent.add("unhealthy")
        
        # Limpiar alertas si el servicio se recupera
        if health["status"] == "healthy":
            self.alerts_sent.clear()
    
    def _send_alert(self, alert_type: str, health_data: Dict[str, Any]):
        """Enviar alerta."""
        alert_message = {
            "alert_type": alert_type,
            "timestamp": self._get_timestamp(),
            "health_data": health_data,
            "service": "weather-agent-a2a"
        }
        
        # Log de la alerta
        logging.error(f"ALERT: {alert_type}", extra=alert_message)
        
        # Enviar webhook si está configurado
        if self.config.alert_webhook_url:
            self._send_webhook_alert(alert_message)
    
    def _send_webhook_alert(self, alert_data: Dict[str, Any]):
        """Enviar alerta por webhook."""
        try:
            import httpx
            
            async def send_webhook():
                async with httpx.AsyncClient() as client:
                    await client.post(
                        self.config.alert_webhook_url,
                        json=alert_data,
                        timeout=10.0
                    )
            
            import asyncio
            asyncio.create_task(send_webhook())
            
        except Exception as e:
            logging.error(f"Error enviando webhook alert: {e}")
    
    def _get_timestamp(self) -> str:
        """Obtener timestamp actual."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


class ProductionSecurity:
    """Configuración de seguridad para producción."""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> set:
        """Cargar API keys válidas."""
        api_keys_env = os.getenv("WEATHER_AGENT_API_KEYS", "")
        if api_keys_env:
            return set(api_keys_env.split(","))
        
        # Cargar desde archivo si existe
        api_keys_file = os.getenv("WEATHER_AGENT_API_KEYS_FILE")
        if api_keys_file and os.path.exists(api_keys_file):
            with open(api_keys_file, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        
        return set()
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validar API key."""
        if not self.config.api_key_required:
            return True
        
        return api_key in self.api_keys
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Obtener configuración CORS."""
        return {
            "allow_origins": self.config.cors_origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["*"],
        }


def create_production_config() -> ProductionConfig:
    """Crear configuración de producción."""
    return ProductionConfig()


def setup_production_environment(config: ProductionConfig) -> Dict[str, Any]:
    """Configurar entorno de producción completo."""
    
    # Configurar logging
    logger = ProductionLogger(config)
    
    # Configurar monitoreo
    monitoring = ProductionMonitoring(config)
    
    # Configurar seguridad
    security = ProductionSecurity(config)
    
    logging.info("Production environment configured", extra={
        "config": {
            "host": config.host,
            "port": config.port,
            "workers": config.workers,
            "cache_enabled": config.cache_enabled,
            "metrics_enabled": config.metrics_enabled,
            "api_key_required": config.api_key_required
        }
    })
    
    return {
        "config": config,
        "logger": logger,
        "monitoring": monitoring,
        "security": security
    } 