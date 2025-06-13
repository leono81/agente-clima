"""
Weather MCP - Cliente MCP para APIs del Clima
=============================================

Cliente MCP que se conecta con Open-Meteo API usando Server-Sent Events (SSE)
para obtener datos meteorológicos en tiempo real.
"""

import asyncio
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
import uuid

import httpx
from sse_starlette import EventSourceResponse

from src.config.settings import get_settings
from src.config.apis import get_weather_config, get_mcp_config
from src.core.models import (
    Location, WeatherRequest, WeatherResponse, CurrentWeather, 
    Forecast, HourlyWeather, DailyWeather, RequestType,
    weather_code_to_condition
)
from src.utils.logging import (
    log_mcp_call, log_weather_request, log_weather_response,
    WeatherOperationSpan, log_error, log_info
)
from src.utils.validators import validate_weather_data, LocationValidator


class WeatherMCPClient:
    """Cliente MCP para APIs del clima."""
    
    def __init__(self):
        self.settings = get_settings()
        self.weather_config = get_weather_config()
        self.mcp_config = get_mcp_config()
        self.http_client = httpx.AsyncClient(timeout=self.settings.weather_api_timeout)
        self.session_id = str(uuid.uuid4())
    
    async def __aenter__(self):
        """Entrada del context manager."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Salida del context manager."""
        await self.disconnect()
    
    async def connect(self):
        """Conectar al servidor MCP Weather."""
        try:
            log_info("Iniciando cliente Weather con conexión directa a Open-Meteo")
            # Usar conexión directa a Open-Meteo API (sin servidor MCP intermedio)
            log_info("Cliente Weather configurado para conexión directa")
                
        except Exception as e:
            log_error(f"Error configurando cliente Weather: {e}")
            # Continuar con conexión directa
    
    async def disconnect(self):
        """Desconectar del cliente HTTP."""
        await self.http_client.aclose()
        log_info("Cliente MCP Weather desconectado")
    
    @log_mcp_call("get_current_weather")
    async def get_current_weather(self, location: Location) -> Optional[CurrentWeather]:
        """Obtener clima actual para una ubicación."""
        
        with WeatherOperationSpan("current_weather", location.name):
            log_weather_request(location.name, "current", coordinates=f"{location.latitude},{location.longitude}")
            
            try:
                # Verificar coordenadas
                if not location.latitude or not location.longitude:
                    coordinates = await self._geocode_location(location.name)
                    if not coordinates:
                        log_error(f"No se pudieron obtener coordenadas para {location.name}")
                        return None
                    location.latitude, location.longitude = coordinates
                
                # Preparar parámetros para la API
                params = {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "current": ",".join(self.weather_config.current_variables),
                    **self.weather_config.default_params
                }
                
                # Hacer solicitud a Open-Meteo
                url = f"{self.weather_config.base_url}{self.weather_config.forecast_endpoint}"
                response = await self.http_client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Validar respuesta
                if "current" not in data:
                    log_error("Respuesta de API sin datos actuales")
                    return None
                
                current_data = data["current"]
                
                # Crear objeto CurrentWeather
                current_weather = CurrentWeather(
                    location=location,
                    timestamp=datetime.fromisoformat(current_data["time"].replace("Z", "+00:00")),
                    temperature=current_data.get("temperature_2m"),
                    apparent_temperature=current_data.get("apparent_temperature"),
                    humidity=current_data.get("relative_humidity_2m"),
                    pressure=current_data.get("pressure_msl"),
                    wind_speed=current_data.get("wind_speed_10m"),
                    wind_direction=current_data.get("wind_direction_10m"),
                    wind_gusts=current_data.get("wind_gusts_10m"),
                    precipitation=current_data.get("precipitation"),
                    cloud_cover=current_data.get("cloud_cover"),
                    visibility=current_data.get("visibility"),
                    weather_code=current_data.get("weather_code"),
                    weather_condition=weather_code_to_condition(current_data.get("weather_code", 0)),
                    is_day=bool(current_data.get("is_day", 1))
                )
                
                # Validar datos meteorológicos
                weather_dict = current_weather.dict()
                is_valid, errors = validate_weather_data(weather_dict)
                if not is_valid:
                    log_error(f"Datos meteorológicos inválidos: {errors}")
                
                log_weather_response(location.name, "success", temperature=current_weather.temperature)
                return current_weather
                
            except httpx.HTTPStatusError as e:
                log_error(f"Error HTTP en API del clima: {e.response.status_code}")
                return None
            except Exception as e:
                log_error(f"Error obteniendo clima actual: {e}")
                return None
    
    @log_mcp_call("search_location")
    async def search_location(self, query: str, limit: int = 5) -> List[Location]:
        """Buscar ubicaciones por nombre."""
        
        with WeatherOperationSpan("location_search", query):
            log_info(f"Buscando ubicación: {query}")
            
            try:
                # Validar query
                if not LocationValidator.validate_city_name(query):
                    log_error(f"Nombre de ubicación inválido: {query}")
                    return []
                
                params = {
                    "name": query.strip(),
                    "count": limit,
                    "language": "es",
                    "format": "json"
                }
                
                response = await self.http_client.get(
                    self.weather_config.geocoding_endpoint,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                
                locations = []
                if "results" in data:
                    for result in data["results"]:
                        location = Location(
                            name=result.get("name", ""),
                            latitude=result.get("latitude"),
                            longitude=result.get("longitude"),
                            country=result.get("country", ""),
                            region=result.get("admin1", ""),
                            timezone=result.get("timezone", ""),
                            elevation=result.get("elevation")
                        )
                        locations.append(location)
                
                log_info(f"Encontradas {len(locations)} ubicaciones para '{query}'")
                return locations
                
            except Exception as e:
                log_error(f"Error buscando ubicación: {e}")
                return []
    
    async def _geocode_location(self, location_name: str) -> Optional[tuple[float, float]]:
        """Obtener coordenadas de una ubicación."""
        locations = await self.search_location(location_name, limit=1)
        if locations and locations[0].latitude and locations[0].longitude:
            return locations[0].latitude, locations[0].longitude
        return None

    @log_mcp_call("get_forecast")
    async def get_forecast(self, location: Location, days: int = 7) -> Optional[Forecast]:
        """Obtener pronóstico meteorológico para una ubicación."""
        
        with WeatherOperationSpan("forecast", location.name):
            log_weather_request(location.name, "forecast", days=days)
            
            try:
                # Verificar coordenadas
                if not location.latitude or not location.longitude:
                    coordinates = await self._geocode_location(location.name)
                    if not coordinates:
                        log_error(f"No se pudieron obtener coordenadas para {location.name}")
                        return None
                    location.latitude, location.longitude = coordinates
                
                # Preparar parámetros para la API
                params = {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,weather_code",
                    "forecast_days": min(days, 16),  # Máximo 16 días
                    **self.weather_config.default_params
                }
                
                # Hacer solicitud a Open-Meteo
                url = f"{self.weather_config.base_url}{self.weather_config.forecast_endpoint}"
                response = await self.http_client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Validar respuesta
                if "daily" not in data:
                    log_error("Respuesta de API sin datos de pronóstico")
                    return None
                
                daily_data = data["daily"]
                
                # Crear objetos DailyWeather
                from src.core.models import DailyWeather, Forecast
                from datetime import date as date_type
                
                daily_forecasts = []
                for i in range(len(daily_data["time"])):
                    daily_weather = DailyWeather(
                        date=date_type.fromisoformat(daily_data["time"][i]),
                        temperature_max=daily_data["temperature_2m_max"][i],
                        temperature_min=daily_data["temperature_2m_min"][i],
                        precipitation_sum=daily_data.get("precipitation_sum", [None])[i],
                        wind_speed_max=daily_data.get("wind_speed_10m_max", [None])[i],
                        weather_code=daily_data.get("weather_code", [None])[i],
                        weather_condition=weather_code_to_condition(daily_data.get("weather_code", [0])[i])
                    )
                    daily_forecasts.append(daily_weather)
                
                # Crear objeto Forecast
                forecast = Forecast(
                    location=location,
                    generated_at=datetime.utcnow(),
                    daily_data=daily_forecasts
                )
                
                log_weather_response(location.name, "success", days=len(daily_forecasts))
                return forecast
                
            except httpx.HTTPStatusError as e:
                log_error(f"Error HTTP en API del pronóstico: {e.response.status_code}")
                return None
            except Exception as e:
                log_error(f"Error obteniendo pronóstico: {e}")
                return None


class WeatherService:
    """Servicio de alto nivel para operaciones meteorológicas."""
    
    def __init__(self):
        self.mcp_client = WeatherMCPClient()
    
    async def get_weather_by_location(self, location_query: str) -> Optional[WeatherResponse]:
        """Obtener clima por nombre de ubicación."""
        
        async with self.mcp_client:
            # Buscar ubicación
            locations = await self.mcp_client.search_location(location_query, limit=1)
            if not locations:
                return WeatherResponse(
                    request_id=str(uuid.uuid4()),
                    status="error",
                    location=Location(name=location_query),
                    error_message=f"No se encontró la ubicación: {location_query}"
                )
            
            location = locations[0]
            
            # Obtener clima actual
            current_weather = await self.mcp_client.get_current_weather(location)
            if not current_weather:
                return WeatherResponse(
                    request_id=str(uuid.uuid4()),
                    status="error",
                    location=location,
                    error_message="No se pudo obtener el clima actual"
                )
            
            return WeatherResponse(
                request_id=str(uuid.uuid4()),
                status="success",
                location=location,
                current_weather=current_weather,
                generated_at=datetime.utcnow()
            )