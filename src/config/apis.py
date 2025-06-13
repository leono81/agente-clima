"""
APIs - Configuración de APIs Externas
=====================================

Configuración centralizada de todos los endpoints y parámetros
de las APIs externas utilizadas por el agente.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class WeatherAPIConfig(BaseModel):
    """Configuración de la API de Open-Meteo."""
    
    base_url: HttpUrl = "https://api.open-meteo.com/v1"
    forecast_endpoint: str = "/forecast"
    geocoding_endpoint: str = "https://geocoding-api.open-meteo.com/v1/search"
    
    # Parámetros por defecto
    default_params: Dict[str, str] = {
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "timeformat": "iso8601",
        "timezone": "auto"
    }
    
    # Variables meteorológicas disponibles (capa gratuita)
    current_variables: List[str] = [
        "temperature_2m",
        "relative_humidity_2m", 
        "apparent_temperature",
        "is_day",
        "precipitation",
        "rain",
        "showers",
        "snowfall",
        "weather_code",
        "cloud_cover",
        "pressure_msl",
        "surface_pressure",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m"
    ]
    
    hourly_variables: List[str] = [
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "apparent_temperature",
        "precipitation_probability",
        "precipitation",
        "rain",
        "showers",
        "snowfall",
        "snow_depth",
        "weather_code",
        "pressure_msl",
        "surface_pressure",
        "cloud_cover",
        "visibility",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
        "uv_index"
    ]
    
    daily_variables: List[str] = [
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "apparent_temperature_max",
        "apparent_temperature_min",
        "sunrise",
        "sunset",
        "uv_index_max",
        "precipitation_sum",
        "rain_sum",
        "showers_sum",
        "snowfall_sum",
        "precipitation_hours",
        "precipitation_probability_max",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "wind_direction_10m_dominant"
    ]


class MCPWeatherConfig(BaseModel):
    """Configuración del servidor MCP Weather SSE."""
    
    server_url: HttpUrl = "http://localhost:8000"
    sse_endpoint: str = "/sse"
    tools_endpoint: str = "/tools"
    
    # Configuración SSE
    sse_retry_delay: int = 5000  # ms
    sse_timeout: int = 30  # seconds
    max_retries: int = 3
    
    # Tools disponibles
    available_tools: List[str] = [
        "get_current_weather",
        "get_forecast",
        "search_location",
        "get_weather_alerts"
    ]


class A2AConfig(BaseModel):
    """Configuración del protocolo Agent-to-Agent."""
    
    protocol_version: str = "1.0"
    message_format: str = "json-rpc-2.0"
    
    # Endpoints A2A
    discovery_endpoint: str = "/a2a/discovery"
    tasks_endpoint: str = "/a2a/tasks"
    status_endpoint: str = "/a2a/status"
    
    # Configuración de timeouts
    task_timeout: int = 120  # seconds
    heartbeat_interval: int = 30  # seconds
    
    # Tipos de tareas soportadas
    supported_task_types: List[str] = [
        "weather_query",
        "forecast_request", 
        "location_search",
        "weather_alert"
    ]


class AgentUIConfig(BaseModel):
    """Configuración de Agent UI."""
    
    ui_url: HttpUrl = "http://localhost:3000"
    api_endpoint: str = "/api/agent"
    
    # Configuración de la interfaz
    theme: str = "light"
    language: str = "es"
    enable_streaming: bool = True
    
    # Features habilitadas
    features: Dict[str, bool] = {
        "voice_input": False,
        "file_upload": False,
        "chat_history": True,
        "export_chat": True,
        "dark_mode": True
    }


class SecurityConfig(BaseModel):
    """Configuración de seguridad."""
    
    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # seconds
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000"
    ]
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: List[str] = ["*"]
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds


class APIConfiguration(BaseModel):
    """Configuración completa de todas las APIs."""
    
    weather_api: WeatherAPIConfig = Field(default_factory=WeatherAPIConfig)
    mcp_weather: MCPWeatherConfig = Field(default_factory=MCPWeatherConfig)
    a2a: A2AConfig = Field(default_factory=A2AConfig)
    agent_ui: AgentUIConfig = Field(default_factory=AgentUIConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)


# Instancia global de configuración de APIs
api_config = APIConfiguration()


def get_weather_config() -> WeatherAPIConfig:
    """Obtener configuración de Weather API."""
    return api_config.weather_api


def get_mcp_config() -> MCPWeatherConfig:
    """Obtener configuración de MCP Weather."""
    return api_config.mcp_weather


def get_a2a_config() -> A2AConfig:
    """Obtener configuración A2A."""
    return api_config.a2a


def get_ui_config() -> AgentUIConfig:
    """Obtener configuración de Agent UI."""
    return api_config.agent_ui


def get_security_config() -> SecurityConfig:
    """Obtener configuración de seguridad."""
    return api_config.security 