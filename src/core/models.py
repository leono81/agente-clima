"""
Models - Modelos Pydantic para Datos
===================================

Modelos Pydantic para validación y serialización de todos los datos
utilizados por el agente del clima.
"""

from datetime import datetime
from datetime import date as date_type
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, validator


# Enums para valores categóricos

class WeatherCondition(str, Enum):
    """Códigos de condiciones meteorológicas."""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    FOG = "fog"
    DRIZZLE = "drizzle"
    RAIN = "rain"
    SNOW = "snow"
    THUNDERSTORM = "thunderstorm"
    UNKNOWN = "unknown"


class RequestType(str, Enum):
    """Tipos de solicitudes meteorológicas."""
    CURRENT = "current"
    FORECAST = "forecast"
    HISTORICAL = "historical"


class TaskStatus(str, Enum):
    """Estados de tareas A2A."""
    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"


class TemperatureUnit(str, Enum):
    """Unidades de temperatura."""
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


class WindSpeedUnit(str, Enum):
    """Unidades de velocidad del viento."""
    KMH = "kmh"
    MS = "ms"
    MPH = "mph"
    KNOTS = "kn"


# Modelos base

class Location(BaseModel):
    """Modelo para ubicaciones geográficas."""
    
    name: str = Field(..., min_length=2, max_length=100, description="Nombre de la ubicación")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitud")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitud")
    country: Optional[str] = Field(None, max_length=50, description="País")
    region: Optional[str] = Field(None, max_length=50, description="Región/Estado")
    timezone: Optional[str] = Field(None, description="Zona horaria")
    elevation: Optional[float] = Field(None, description="Elevación en metros")


class WeatherData(BaseModel):
    """Modelo base para datos meteorológicos."""
    
    timestamp: datetime = Field(..., description="Timestamp de los datos")
    temperature: Optional[float] = Field(None, description="Temperatura (°C)")
    temperature_max: Optional[float] = Field(None, description="Temperatura máxima (°C)")
    temperature_min: Optional[float] = Field(None, description="Temperatura mínima (°C)")
    apparent_temperature: Optional[float] = Field(None, description="Temperatura aparente (°C)")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humedad relativa (%)")
    pressure: Optional[float] = Field(None, description="Presión atmosférica (hPa)")
    wind_speed: Optional[float] = Field(None, ge=0, description="Velocidad del viento (km/h)")
    wind_direction: Optional[float] = Field(None, ge=0, le=360, description="Dirección del viento (grados)")
    wind_gusts: Optional[float] = Field(None, ge=0, description="Ráfagas de viento (km/h)")
    precipitation: Optional[float] = Field(None, ge=0, description="Precipitación (mm)")
    precipitation_probability: Optional[float] = Field(None, ge=0, le=100, description="Probabilidad de precipitación (%)")
    cloud_cover: Optional[float] = Field(None, ge=0, le=100, description="Cobertura nubosa (%)")
    visibility: Optional[float] = Field(None, ge=0, description="Visibilidad (km)")
    uv_index: Optional[float] = Field(None, ge=0, description="Índice UV")
    weather_code: Optional[int] = Field(None, description="Código de condición meteorológica")
    weather_condition: Optional[WeatherCondition] = Field(None, description="Condición meteorológica")
    is_day: Optional[bool] = Field(None, description="Es de día")


class CurrentWeather(WeatherData):
    """Modelo para datos meteorológicos actuales."""
    
    location: Location = Field(..., description="Ubicación")


class HourlyWeather(WeatherData):
    """Modelo para datos meteorológicos por hora."""
    
    pass


class DailyWeather(BaseModel):
    """Modelo para datos meteorológicos diarios."""
    
    date: date_type = Field(..., description="Fecha")
    temperature_max: Optional[float] = Field(None, description="Temperatura máxima (°C)")
    temperature_min: Optional[float] = Field(None, description="Temperatura mínima (°C)")
    apparent_temperature_max: Optional[float] = Field(None, description="Temperatura aparente máxima (°C)")
    apparent_temperature_min: Optional[float] = Field(None, description="Temperatura aparente mínima (°C)")
    precipitation_sum: Optional[float] = Field(None, ge=0, description="Precipitación total (mm)")
    precipitation_hours: Optional[float] = Field(None, ge=0, description="Horas de precipitación")
    precipitation_probability_max: Optional[float] = Field(None, ge=0, le=100, description="Probabilidad máxima de precipitación (%)")
    wind_speed_max: Optional[float] = Field(None, ge=0, description="Velocidad máxima del viento (km/h)")
    wind_gusts_max: Optional[float] = Field(None, ge=0, description="Ráfagas máximas del viento (km/h)")
    wind_direction_dominant: Optional[float] = Field(None, ge=0, le=360, description="Dirección dominante del viento (grados)")
    sunrise: Optional[datetime] = Field(None, description="Hora de salida del sol")
    sunset: Optional[datetime] = Field(None, description="Hora de puesta del sol")
    uv_index_max: Optional[float] = Field(None, ge=0, description="Índice UV máximo")
    weather_code: Optional[int] = Field(None, description="Código de condición meteorológica")
    weather_condition: Optional[WeatherCondition] = Field(None, description="Condición meteorológica")


class Forecast(BaseModel):
    """Modelo para pronósticos meteorológicos."""
    
    location: Location = Field(..., description="Ubicación")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de generación")
    hourly_data: Optional[List[HourlyWeather]] = Field(default_factory=list, description="Datos por hora")
    daily_data: Optional[List[DailyWeather]] = Field(default_factory=list, description="Datos diarios")


# Modelos para solicitudes y respuestas

class WeatherRequest(BaseModel):
    """Modelo para solicitudes meteorológicas."""
    
    request_id: str = Field(..., description="ID único de la solicitud")
    request_type: RequestType = Field(..., description="Tipo de solicitud")
    location: Location = Field(..., description="Ubicación solicitada")
    start_date: Optional[date_type] = Field(None, description="Fecha de inicio")
    end_date: Optional[date_type] = Field(None, description="Fecha de fin")
    parameters: Optional[List[str]] = Field(default_factory=list, description="Parámetros específicos solicitados")
    temperature_unit: TemperatureUnit = Field(default=TemperatureUnit.CELSIUS, description="Unidad de temperatura")
    wind_speed_unit: WindSpeedUnit = Field(default=WindSpeedUnit.KMH, description="Unidad de velocidad del viento")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de la solicitud")


class WeatherResponse(BaseModel):
    """Modelo para respuestas meteorológicas."""
    
    request_id: str = Field(..., description="ID de la solicitud")
    status: str = Field(..., description="Estado de la respuesta")
    location: Location = Field(..., description="Ubicación")
    current_weather: Optional[CurrentWeather] = Field(None, description="Datos actuales")
    forecast: Optional[Forecast] = Field(None, description="Pronóstico")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de generación")
    source: str = Field(default="Open-Meteo", description="Fuente de los datos")
    error_message: Optional[str] = Field(None, description="Mensaje de error si aplica")


# Modelos para MCP

class MCPToolCall(BaseModel):
    """Modelo para llamadas a herramientas MCP."""
    
    tool_name: str = Field(..., description="Nombre de la herramienta")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros de la herramienta")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de la llamada")


class MCPToolResponse(BaseModel):
    """Modelo para respuestas de herramientas MCP."""
    
    tool_name: str = Field(..., description="Nombre de la herramienta")
    status: str = Field(..., description="Estado de la respuesta")
    result: Any = Field(None, description="Resultado de la herramienta")
    error: Optional[str] = Field(None, description="Error si aplica")
    execution_time_ms: Optional[float] = Field(None, description="Tiempo de ejecución en ms")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de la respuesta")


# Modelos para A2A

class A2AMessage(BaseModel):
    """Modelo base para mensajes A2A."""
    
    jsonrpc: str = Field(default="2.0", description="Versión JSON-RPC")
    method: str = Field(..., description="Método del mensaje")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parámetros del mensaje")
    id: str = Field(..., description="ID único del mensaje")


class A2ARequest(A2AMessage):
    """Modelo para solicitudes A2A."""
    
    agent_id: str = Field(..., description="ID del agente solicitante")
    task_type: str = Field(..., description="Tipo de tarea")
    priority: int = Field(default=1, ge=1, le=5, description="Prioridad de la tarea")
    timeout: int = Field(default=120, description="Timeout en segundos")


class A2AResponse(BaseModel):
    """Modelo para respuestas A2A."""
    
    jsonrpc: str = Field(default="2.0", description="Versión JSON-RPC")
    result: Optional[Any] = Field(None, description="Resultado")
    error: Optional[Dict[str, Any]] = Field(None, description="Error")
    id: str = Field(..., description="ID del mensaje original")


class A2ATask(BaseModel):
    """Modelo para tareas A2A."""
    
    task_id: str = Field(..., description="ID único de la tarea")
    agent_id: str = Field(..., description="ID del agente")
    task_type: str = Field(..., description="Tipo de tarea")
    status: TaskStatus = Field(default=TaskStatus.SUBMITTED, description="Estado de la tarea")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Datos de la tarea")
    result: Optional[Any] = Field(None, description="Resultado de la tarea")
    error: Optional[str] = Field(None, description="Error si aplica")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de creación")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de actualización")
    completed_at: Optional[datetime] = Field(None, description="Timestamp de completado")


# Modelos para Agent UI

class ChatMessage(BaseModel):
    """Modelo para mensajes de chat."""
    
    message_id: str = Field(..., description="ID único del mensaje")
    role: str = Field(..., pattern=r'^(user|assistant|system)$', description="Rol del mensaje")
    content: str = Field(..., description="Contenido del mensaje")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp del mensaje")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadatos adicionales")


class ChatSession(BaseModel):
    """Modelo para sesiones de chat."""
    
    session_id: str = Field(..., description="ID único de la sesión")
    user_id: Optional[str] = Field(None, description="ID del usuario")
    messages: List[ChatMessage] = Field(default_factory=list, description="Mensajes de la sesión")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de creación")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de actualización")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadatos de la sesión")


# Modelos para configuración

class AgentConfig(BaseModel):
    """Modelo para configuración del agente."""
    
    agent_id: str = Field(..., description="ID único del agente")
    name: str = Field(..., description="Nombre del agente")
    version: str = Field(..., description="Versión del agente")
    description: str = Field(..., description="Descripción del agente")
    capabilities: List[str] = Field(default_factory=list, description="Capacidades del agente")
    supported_languages: List[str] = Field(default=["es", "en"], description="Idiomas soportados")
    max_concurrent_requests: int = Field(default=10, description="Máximo de solicitudes concurrentes")
    timeout_seconds: int = Field(default=30, description="Timeout por defecto")
    rate_limit: int = Field(default=100, description="Límite de rate por minuto")


# Funciones de utilidad para conversión de datos meteorológicos

def weather_code_to_condition(code: int) -> WeatherCondition:
    """Convertir código WMO a condición meteorológica."""
    code_mapping = {
        0: WeatherCondition.CLEAR,
        1: WeatherCondition.PARTLY_CLOUDY,
        2: WeatherCondition.PARTLY_CLOUDY,
        3: WeatherCondition.CLOUDY,
        45: WeatherCondition.FOG,
        48: WeatherCondition.FOG,
        51: WeatherCondition.DRIZZLE,
        53: WeatherCondition.DRIZZLE,
        55: WeatherCondition.DRIZZLE,
        61: WeatherCondition.RAIN,
        63: WeatherCondition.RAIN,
        65: WeatherCondition.RAIN,
        71: WeatherCondition.SNOW,
        73: WeatherCondition.SNOW,
        75: WeatherCondition.SNOW,
        95: WeatherCondition.THUNDERSTORM,
        96: WeatherCondition.THUNDERSTORM,
        99: WeatherCondition.THUNDERSTORM,
    }
    
    return code_mapping.get(code, WeatherCondition.UNKNOWN)


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convertir Celsius a Fahrenheit."""
    return (celsius * 9/5) + 32


def kmh_to_ms(kmh: float) -> float:
    """Convertir km/h a m/s."""
    return kmh / 3.6


def kmh_to_mph(kmh: float) -> float:
    """Convertir km/h a mph."""
    return kmh * 0.621371 