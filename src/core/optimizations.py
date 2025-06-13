#!/usr/bin/env python3
"""
A2A Performance Optimizations
=============================

Sistema de optimizaciones de rendimiento para comunicación A2A:
- Connection pooling
- Caching inteligente
- Rate limiting
- Circuit breaker
- Métricas y monitoreo
"""

import asyncio
import time
import hashlib
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import httpx
from functools import wraps
import json


@dataclass
class CacheEntry:
    """Entrada de cache con TTL."""
    data: Any
    timestamp: float
    ttl: float
    
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl


@dataclass
class CircuitBreakerState:
    """Estado del circuit breaker."""
    failure_count: int = 0
    last_failure_time: float = 0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    
    def should_allow_request(self) -> bool:
        """Determinar si se debe permitir la solicitud."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Registrar éxito."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Registrar fallo."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


@dataclass
class RateLimitBucket:
    """Bucket para rate limiting."""
    tokens: float
    last_refill: float
    capacity: float
    refill_rate: float  # tokens per second
    
    def consume(self, tokens: float = 1.0) -> bool:
        """Consumir tokens del bucket."""
        now = time.time()
        
        # Rellenar bucket
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
        
        # Verificar si hay suficientes tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


@dataclass
class PerformanceMetrics:
    """Métricas de rendimiento."""
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_latency: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    circuit_breaker_trips: int = 0
    rate_limit_rejections: int = 0
    
    def record_request(self, latency: float, success: bool):
        """Registrar solicitud."""
        self.request_count += 1
        self.total_latency += latency
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_average_latency(self) -> float:
        """Obtener latencia promedio."""
        return self.total_latency / max(1, self.request_count)
    
    def get_success_rate(self) -> float:
        """Obtener tasa de éxito."""
        return self.success_count / max(1, self.request_count)
    
    def get_cache_hit_rate(self) -> float:
        """Obtener tasa de cache hits."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / max(1, total)


class IntelligentCache:
    """Cache inteligente con TTL y LRU."""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: deque = deque()
        self.metrics = PerformanceMetrics()
    
    def _generate_key(self, method: str, params: Dict[str, Any]) -> str:
        """Generar clave de cache."""
        # Crear clave determinística basada en método y parámetros
        content = f"{method}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, method: str, params: Dict[str, Any]) -> Optional[Any]:
        """Obtener valor del cache."""
        key = self._generate_key(method, params)
        
        if key in self.cache:
            entry = self.cache[key]
            
            if not entry.is_expired():
                # Mover al final (más reciente)
                self.access_order.remove(key)
                self.access_order.append(key)
                self.metrics.cache_hits += 1
                return entry.data
            else:
                # Eliminar entrada expirada
                del self.cache[key]
                self.access_order.remove(key)
        
        self.metrics.cache_misses += 1
        return None
    
    def set(self, method: str, params: Dict[str, Any], data: Any, ttl: Optional[float] = None):
        """Establecer valor en cache."""
        key = self._generate_key(method, params)
        ttl = ttl or self.default_ttl
        
        # Eliminar entradas si se alcanza el límite
        while len(self.cache) >= self.max_size and self.access_order:
            oldest_key = self.access_order.popleft()
            if oldest_key in self.cache:
                del self.cache[oldest_key]
        
        # Agregar nueva entrada
        self.cache[key] = CacheEntry(data, time.time(), ttl)
        
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def clear_expired(self):
        """Limpiar entradas expiradas."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": self.metrics.get_cache_hit_rate(),
            "hits": self.metrics.cache_hits,
            "misses": self.metrics.cache_misses
        }


class ConnectionPool:
    """Pool de conexiones HTTP optimizado."""
    
    def __init__(self, max_connections: int = 100, max_keepalive: int = 20):
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
    
    async def get_client(self) -> httpx.AsyncClient:
        """Obtener cliente HTTP con pool de conexiones."""
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    limits = httpx.Limits(
                        max_connections=self.max_connections,
                        max_keepalive_connections=self.max_keepalive
                    )
                    
                    timeout = httpx.Timeout(
                        connect=10.0,
                        read=30.0,
                        write=10.0,
                        pool=5.0
                    )
                    
                    self._client = httpx.AsyncClient(
                        limits=limits,
                        timeout=timeout,
                        http2=True  # Habilitar HTTP/2 para mejor rendimiento
                    )
        
        return self._client
    
    async def close(self):
        """Cerrar pool de conexiones."""
        if self._client:
            await self._client.aclose()
            self._client = None


class A2AOptimizer:
    """Optimizador principal para comunicación A2A."""
    
    def __init__(self):
        self.cache = IntelligentCache()
        self.connection_pool = ConnectionPool()
        self.circuit_breakers: Dict[str, CircuitBreakerState] = defaultdict(CircuitBreakerState)
        self.rate_limiters: Dict[str, RateLimitBucket] = {}
        self.metrics = PerformanceMetrics()
        
        # Configuración por defecto
        self.cache_ttl_config = {
            "search_locations": 3600,  # 1 hora
            "get_current_weather": 300,  # 5 minutos
            "get_forecast": 1800,  # 30 minutos
            "get_agent_info": 86400,  # 24 horas
            "get_capabilities": 86400,  # 24 horas
        }
        
        # Configurar rate limiters por defecto
        self._setup_default_rate_limiters()
    
    def _setup_default_rate_limiters(self):
        """Configurar rate limiters por defecto."""
        # Rate limiter global: 100 requests/minuto
        self.rate_limiters["global"] = RateLimitBucket(
            tokens=100.0,
            last_refill=time.time(),
            capacity=100.0,
            refill_rate=100.0 / 60.0  # 100 tokens per minute
        )
        
        # Rate limiter por método
        for method in ["get_current_weather", "search_locations", "get_forecast"]:
            self.rate_limiters[method] = RateLimitBucket(
                tokens=50.0,
                last_refill=time.time(),
                capacity=50.0,
                refill_rate=50.0 / 60.0  # 50 tokens per minute
            )
    
    def cache_decorator(self, method: str, ttl: Optional[float] = None):
        """Decorador para cachear resultados de métodos."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extraer parámetros para la clave de cache
                params = kwargs.copy()
                
                # Intentar obtener del cache
                cached_result = self.cache.get(method, params)
                if cached_result is not None:
                    return cached_result
                
                # Ejecutar función original
                result = await func(*args, **kwargs)
                
                # Guardar en cache si es exitoso
                if result and getattr(result, 'status', None) == 'success':
                    cache_ttl = ttl or self.cache_ttl_config.get(method, 300)
                    self.cache.set(method, params, result, cache_ttl)
                
                return result
            
            return wrapper
        return decorator
    
    def circuit_breaker_decorator(self, service: str):
        """Decorador para circuit breaker."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                breaker = self.circuit_breakers[service]
                
                if not breaker.should_allow_request():
                    self.metrics.circuit_breaker_trips += 1
                    raise Exception(f"Circuit breaker OPEN for service: {service}")
                
                try:
                    result = await func(*args, **kwargs)
                    breaker.record_success()
                    return result
                except Exception as e:
                    breaker.record_failure()
                    raise e
            
            return wrapper
        return decorator
    
    def rate_limit_decorator(self, limiter_key: str):
        """Decorador para rate limiting."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Verificar rate limit global
                if not self.rate_limiters["global"].consume():
                    self.metrics.rate_limit_rejections += 1
                    raise Exception("Rate limit exceeded: global")
                
                # Verificar rate limit específico
                if limiter_key in self.rate_limiters:
                    if not self.rate_limiters[limiter_key].consume():
                        self.metrics.rate_limit_rejections += 1
                        raise Exception(f"Rate limit exceeded: {limiter_key}")
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def performance_monitor_decorator(self, operation: str):
        """Decorador para monitorear rendimiento."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                success = False
                
                try:
                    result = await func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    raise e
                finally:
                    latency = time.time() - start_time
                    self.metrics.record_request(latency, success)
            
            return wrapper
        return decorator
    
    async def optimize_request(self, method: str, params: Dict[str, Any], 
                             execute_func: Callable) -> Any:
        """Ejecutar solicitud con todas las optimizaciones."""
        
        # Aplicar decoradores dinámicamente
        @self.cache_decorator(method)
        @self.circuit_breaker_decorator("weather_service")
        @self.rate_limit_decorator(method)
        @self.performance_monitor_decorator(method)
        async def optimized_execute():
            return await execute_func(params)
        
        return await optimized_execute()
    
    async def cleanup(self):
        """Limpiar recursos."""
        # Limpiar cache expirado
        self.cache.clear_expired()
        
        # Cerrar pool de conexiones
        await self.connection_pool.close()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Obtener reporte de rendimiento."""
        return {
            "requests": {
                "total": self.metrics.request_count,
                "successful": self.metrics.success_count,
                "failed": self.metrics.error_count,
                "success_rate": f"{self.metrics.get_success_rate():.1%}",
                "average_latency": f"{self.metrics.get_average_latency():.3f}s"
            },
            "cache": self.cache.get_stats(),
            "circuit_breakers": {
                service: {
                    "state": breaker.state,
                    "failure_count": breaker.failure_count
                }
                for service, breaker in self.circuit_breakers.items()
            },
            "rate_limiting": {
                "rejections": self.metrics.rate_limit_rejections,
                "buckets": {
                    key: {
                        "tokens": bucket.tokens,
                        "capacity": bucket.capacity
                    }
                    for key, bucket in self.rate_limiters.items()
                }
            }
        }


# Instancia global del optimizador
global_optimizer = A2AOptimizer()


def get_optimizer() -> A2AOptimizer:
    """Obtener instancia global del optimizador."""
    return global_optimizer 