"""
Validators - Validaciones de Datos
=================================

Validaciones para datos de entrada, coordenadas geográficas,
parámetros meteorológicos y otros datos del agente.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field, field_validator, ValidationError


class LocationValidator:
    """Validador para ubicaciones geográficas."""
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        """Validar coordenadas geográficas."""
        return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)
    
    @staticmethod
    def validate_city_name(city: str) -> bool:
        """Validar nombre de ciudad."""
        if not city or len(city.strip()) < 2:
            return False
        
        # Permitir letras, espacios, guiones, puntos, comas, paréntesis y caracteres especiales comunes
        pattern = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-\.\'\,\(\)]+$'
        return bool(re.match(pattern, city.strip()))
    
    @staticmethod
    def normalize_city_name(city: str) -> str:
        """Normalizar nombre de ciudad."""
        return city.strip().title()


class WeatherParameterValidator:
    """Validador para parámetros meteorológicos."""
    
    # Rangos válidos para parámetros meteorológicos
    TEMPERATURE_RANGE = (-70, 60)  # Celsius
    HUMIDITY_RANGE = (0, 100)  # Porcentaje
    PRESSURE_RANGE = (870, 1085)  # hPa
    WIND_SPEED_RANGE = (0, 500)  # km/h
    PRECIPITATION_RANGE = (0, 1000)  # mm
    
    @classmethod
    def validate_temperature(cls, temp: float) -> bool:
        """Validar temperatura."""
        return cls.TEMPERATURE_RANGE[0] <= temp <= cls.TEMPERATURE_RANGE[1]
    
    @classmethod
    def validate_humidity(cls, humidity: float) -> bool:
        """Validar humedad."""
        return cls.HUMIDITY_RANGE[0] <= humidity <= cls.HUMIDITY_RANGE[1]
    
    @classmethod
    def validate_pressure(cls, pressure: float) -> bool:
        """Validar presión atmosférica."""
        return cls.PRESSURE_RANGE[0] <= pressure <= cls.PRESSURE_RANGE[1]
    
    @classmethod
    def validate_wind_speed(cls, speed: float) -> bool:
        """Validar velocidad del viento."""
        return cls.WIND_SPEED_RANGE[0] <= speed <= cls.WIND_SPEED_RANGE[1]
    
    @classmethod
    def validate_precipitation(cls, precip: float) -> bool:
        """Validar precipitación."""
        return cls.PRECIPITATION_RANGE[0] <= precip <= cls.PRECIPITATION_RANGE[1]


class DateTimeValidator:
    """Validador para fechas y tiempos."""
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date, max_days: int = 16) -> bool:
        """Validar rango de fechas."""
        if start_date > end_date:
            return False
        
        delta = (end_date - start_date).days
        return delta <= max_days
    
    @staticmethod
    def validate_forecast_date(target_date: date) -> bool:
        """Validar fecha para pronóstico (máximo 16 días desde hoy)."""
        today = date.today()
        max_date = today + timedelta(days=16)
        
        return today <= target_date <= max_date
    
    @staticmethod
    def validate_historical_date(target_date: date) -> bool:
        """Validar fecha histórica (desde 1979)."""
        min_date = date(1979, 1, 1)
        today = date.today()
        
        return min_date <= target_date < today


class APIParameterValidator:
    """Validador para parámetros de API."""
    
    VALID_TEMPERATURE_UNITS = ["celsius", "fahrenheit"]
    VALID_WIND_SPEED_UNITS = ["kmh", "ms", "mph", "kn"]
    VALID_PRECIPITATION_UNITS = ["mm", "inch"]
    VALID_TIMEFORMATS = ["iso8601", "unixtime"]
    
    @classmethod
    def validate_temperature_unit(cls, unit: str) -> bool:
        """Validar unidad de temperatura."""
        return unit.lower() in cls.VALID_TEMPERATURE_UNITS
    
    @classmethod
    def validate_wind_speed_unit(cls, unit: str) -> bool:
        """Validar unidad de velocidad del viento."""
        return unit.lower() in cls.VALID_WIND_SPEED_UNITS
    
    @classmethod
    def validate_precipitation_unit(cls, unit: str) -> bool:
        """Validar unidad de precipitación."""
        return unit.lower() in cls.VALID_PRECIPITATION_UNITS
    
    @classmethod
    def validate_time_format(cls, format_str: str) -> bool:
        """Validar formato de tiempo."""
        return format_str.lower() in cls.VALID_TIMEFORMATS


# Modelos Pydantic para validación estructurada

class CoordinatesModel(BaseModel):
    """Modelo para coordenadas geográficas."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitud")
    longitude: float = Field(..., ge=-180, le=180, description="Longitud")
    
    @field_validator('latitude', 'longitude')
    @classmethod
    def validate_precision(cls, v):
        """Validar precisión de coordenadas."""
        # Limitar a 6 decimales (aproximadamente 10cm de precisión)
        return round(v, 6)


class LocationModel(BaseModel):
    """Modelo para ubicación."""
    
    name: str = Field(..., min_length=2, max_length=100, description="Nombre de la ubicación")
    coordinates: Optional[CoordinatesModel] = None
    country: Optional[str] = Field(None, max_length=50, description="País")
    region: Optional[str] = Field(None, max_length=50, description="Región/Estado")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validar y normalizar nombre."""
        if not LocationValidator.validate_city_name(v):
            raise ValueError("Nombre de ubicación inválido")
        return LocationValidator.normalize_city_name(v)


class WeatherRequestModel(BaseModel):
    """Modelo para solicitudes meteorológicas."""
    
    location: LocationModel
    request_type: str = Field(..., pattern=r'^(current|forecast|historical)$')
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    parameters: Optional[List[str]] = Field(default_factory=list)
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_dates(cls, v):
        """Validar fechas según el tipo de solicitud."""
        if v is None:
            return v
        
        # Validación básica de fecha
        if not DateTimeValidator.validate_forecast_date(v):
            raise ValueError("Fecha fuera del rango válido")
        
        return v


class A2AMessageModel(BaseModel):
    """Modelo para mensajes A2A."""
    
    message_id: str = Field(..., pattern=r'^[a-zA-Z0-9\-_]+$')
    agent_id: str = Field(..., min_length=1, max_length=50)
    task_type: str = Field(..., pattern=r'^(weather_query|forecast_request|location_search|weather_alert)$')
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('payload')
    @classmethod
    def validate_payload(cls, v):
        """Validar payload básico."""
        if not isinstance(v, dict):
            raise ValueError("Payload debe ser un diccionario")
        
        return v


# Funciones de validación de alto nivel

def validate_weather_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validar datos meteorológicos completos."""
    errors = []
    
    # Validar temperatura
    if 'temperature' in data:
        if not WeatherParameterValidator.validate_temperature(data['temperature']):
            errors.append(f"Temperatura fuera de rango: {data['temperature']}°C")
    
    # Validar humedad
    if 'humidity' in data:
        if not WeatherParameterValidator.validate_humidity(data['humidity']):
            errors.append(f"Humedad fuera de rango: {data['humidity']}%")
    
    # Validar presión
    if 'pressure' in data:
        if not WeatherParameterValidator.validate_pressure(data['pressure']):
            errors.append(f"Presión fuera de rango: {data['pressure']} hPa")
    
    # Validar viento
    if 'wind_speed' in data:
        if not WeatherParameterValidator.validate_wind_speed(data['wind_speed']):
            errors.append(f"Velocidad del viento fuera de rango: {data['wind_speed']} km/h")
    
    # Validar precipitación
    if 'precipitation' in data:
        if not WeatherParameterValidator.validate_precipitation(data['precipitation']):
            errors.append(f"Precipitación fuera de rango: {data['precipitation']} mm")
    
    return len(errors) == 0, errors


def validate_api_request(request_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validar solicitud completa de API."""
    errors = []
    
    try:
        # Validar usando el modelo Pydantic
        WeatherRequestModel(**request_data)
    except ValidationError as e:
        for error in e.errors():
            field = '.'.join(str(x) for x in error['loc'])
            errors.append(f"{field}: {error['msg']}")
    
    return len(errors) == 0, errors


def sanitize_input(input_str: str) -> str:
    """Sanitizar entrada del usuario."""
    if not input_str:
        return ""
    
    # Remover caracteres potencialmente peligrosos
    sanitized = re.sub(r'[<>"\']', '', input_str)
    
    # Limitar longitud
    sanitized = sanitized[:1000]
    
    # Normalizar espacios
    sanitized = ' '.join(sanitized.split())
    
    return sanitized


def validate_mcp_response(response: Dict[str, Any]) -> bool:
    """Validar respuesta MCP."""
    required_fields = ['status', 'data']
    
    for field in required_fields:
        if field not in response:
            return False
    
    # Validar status
    if response['status'] not in ['success', 'error', 'partial']:
        return False
    
    return True 