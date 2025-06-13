"""
Agent - Agente Principal del Clima con PydanticAI
================================================

Agente inteligente para información meteorológica usando PydanticAI,
con integración completa de OpenAI, MCP Weather y A2A.
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
import uuid

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.core.models import (
    Location, WeatherResponse, CurrentWeather, Forecast,
    RequestType, WeatherCondition, AgentConfig
)
from src.core.weather_mcp import WeatherService
from src.utils.logging import (
    WeatherOperationSpan, log_info, log_error, log_debug,
    log_agent_decision, log_performance_metric
)
from src.utils.validators import sanitize_input, LocationValidator


# Modelos para el contexto del agente

class WeatherContext(BaseModel):
    """Contexto para operaciones meteorológicas."""
    
    user_id: Optional[str] = None
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    preferred_units: str = "metric"
    language: str = "es"
    last_location: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)


class WeatherQuery(BaseModel):
    """Estructura para consultas meteorológicas."""
    
    location: str = Field(..., description="Ubicación para la consulta meteorológica")
    query_type: str = Field(default="current", description="Tipo de consulta: current, forecast, etc.")
    specific_request: Optional[str] = Field(None, description="Solicitud específica del usuario")


# Configuración del agente

def create_weather_agent() -> Agent[WeatherContext, str]:
    """Crear el agente del clima con todas las herramientas."""
    
    settings = get_settings()
    
    # Configurar modelo OpenAI
    # La API key se debe configurar como variable de entorno OPENAI_API_KEY
    import os
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    
    model = OpenAIModel(
        model_name=settings.openai_model
    )
    
    # Crear agente con configuración
    agent = Agent(
        model,
        deps_type=WeatherContext,
        result_type=str,
        system_prompt=get_system_prompt()
    )
    
    return agent


def get_system_prompt() -> str:
    """Obtener el prompt del sistema para el agente."""
    
    return """
    Eres un agente experto en meteorología llamado "Clima Agent". Tu especialidad es proporcionar 
    información meteorológica precisa, actualizada y útil en español.

    CAPACIDADES:
    - Consultar clima actual de cualquier ubicación mundial
    - Proporcionar pronósticos meteorológicos detallados
    - Buscar ubicaciones geográficas
    - Interpretar datos meteorológicos complejos
    - Dar recomendaciones basadas en condiciones climáticas

    ESTILO DE COMUNICACIÓN:
    - Siempre en español argentino
    - Amigable y profesional
    - Claro y conciso
    - Incluye detalles relevantes sin ser abrumador
    - Usa emojis meteorológicos apropiados (☀️🌧️❄️🌤️⛅☁️🌩️)

    FORMATO DE RESPUESTAS:
    - Para clima actual: temperatura, sensación térmica, humedad, viento, condición
    - Para pronósticos: resumen por días con temperaturas min/max
    - Siempre incluir la ubicación confirmada
    - Mencionar la fuente de datos (Open-Meteo)
    - Agregar timestamp de los datos

    INSTRUCCIONES ESPECIALES:
    - Si la ubicación es ambigua, pregunta por aclaración
    - Si no encuentras una ubicación, sugiere alternativas
    - Para pronósticos largos, resume los puntos más importantes
    - Incluye consejos prácticos cuando sea relevante
    - Si hay condiciones extremas, menciona precauciones

    Siempre usa las herramientas disponibles para obtener datos actualizados.
    """


# Crear instancia del agente
weather_agent = create_weather_agent()


@weather_agent.tool
async def get_current_weather_tool(ctx: RunContext[WeatherContext], location: str) -> str:
    """Obtener el clima actual para una ubicación específica."""
    
    location = sanitize_input(location)
    
    with WeatherOperationSpan("get_current_weather", location):
        log_info(f"Obteniendo clima actual para: {location}")
        
        try:
            weather_service = WeatherService()
            response = await weather_service.get_weather_by_location(location)
            
            if not response or response.status == "error":
                error_msg = response.error_message if response else "Error desconocido"
                log_error(f"Error obteniendo clima: {error_msg}")
                return f"❌ No pude obtener el clima para '{location}'. {error_msg}"
            
            current = response.current_weather
            loc = response.location
            
            # Actualizar contexto
            ctx.deps.last_location = location
            
            # Formatear respuesta
            condition_emoji = get_condition_emoji(current.weather_condition)
            
            result = f"""
🌍 **{loc.name}**{f", {loc.country}" if loc.country else ""}

{condition_emoji} **{current.weather_condition.value.replace('_', ' ').title()}**

🌡️ **Temperatura:** {current.temperature:.1f}°C
🔥 **Sensación térmica:** {current.apparent_temperature:.1f}°C
💧 **Humedad:** {current.humidity:.0f}%
🌬️ **Viento:** {current.wind_speed:.1f} km/h {get_wind_direction(current.wind_direction)}
📊 **Presión:** {current.pressure:.0f} hPa
☁️ **Nubosidad:** {current.cloud_cover:.0f}%

📅 *Datos de {current.timestamp.strftime('%H:%M')} - Fuente: Open-Meteo*
            """.strip()
            
            log_info(f"Clima obtenido exitosamente para {location}")
            return result
            
        except Exception as e:
            log_error(f"Error en get_current_weather_tool: {e}")
            return f"❌ Error interno obteniendo el clima para '{location}'. Por favor intenta de nuevo."


@weather_agent.tool
async def search_locations_tool(ctx: RunContext[WeatherContext], query: str) -> str:
    """Buscar ubicaciones geográficas que coincidan con la consulta."""
    
    query = sanitize_input(query)
    
    with WeatherOperationSpan("search_locations", query):
        log_info(f"Buscando ubicaciones para: {query}")
        
        try:
            weather_service = WeatherService()
            
            async with weather_service.mcp_client:
                locations = await weather_service.mcp_client.search_location(query, limit=5)
            
            if not locations:
                return f"❌ No encontré ubicaciones para '{query}'. Intenta con un nombre más específico."
            
            result = f"📍 **Ubicaciones encontradas para '{query}':**\n\n"
            
            for i, loc in enumerate(locations, 1):
                country_info = f", {loc.country}" if loc.country else ""
                region_info = f" ({loc.region})" if loc.region else ""
                
                result += f"{i}. **{loc.name}**{country_info}{region_info}\n"
                result += f"   📍 {loc.latitude:.2f}, {loc.longitude:.2f}\n\n"
            
            result += "💡 *Usa el nombre completo de la ubicación para obtener el clima*"
            
            log_info(f"Encontradas {len(locations)} ubicaciones para '{query}'")
            return result
            
        except Exception as e:
            log_error(f"Error en search_locations_tool: {e}")
            return f"❌ Error buscando ubicaciones para '{query}'. Por favor intenta de nuevo."


@weather_agent.tool
async def get_weather_forecast_tool(ctx: RunContext[WeatherContext], location: str, days: int = 7) -> str:
    """Obtener pronóstico meteorológico para una ubicación."""
    
    location = sanitize_input(location)
    days = min(max(days, 1), 16)  # Limitar entre 1 y 16 días
    
    with WeatherOperationSpan("get_weather_forecast", location):
        log_info(f"Obteniendo pronóstico para: {location}, días: {days}")
        
        try:
            weather_service = WeatherService()
            
            async with weather_service.mcp_client:
                # Buscar ubicación
                locations = await weather_service.mcp_client.search_location(location, limit=1)
                if not locations:
                    return f"❌ No encontré la ubicación '{location}'"
                
                loc = locations[0]
                
                # Obtener pronóstico
                forecast = await weather_service.mcp_client.get_forecast(loc, days=days)
                if not forecast:
                    return f"❌ No pude obtener el pronóstico para '{location}'"
            
            # Actualizar contexto
            ctx.deps.last_location = location
            
            # Formatear respuesta
            result = f"🌍 **Pronóstico para {loc.name}**{f', {loc.country}' if loc.country else ''}\n\n"
            
            if forecast.daily_data:
                for day_data in forecast.daily_data[:days]:
                    condition_emoji = get_condition_emoji(day_data.weather_condition)
                    day_name = get_day_name(day_data.date)
                    
                    result += f"📅 **{day_name} ({day_data.date.strftime('%d/%m')})**\n"
                    result += f"{condition_emoji} {day_data.weather_condition.value.replace('_', ' ').title()}\n"
                    result += f"🌡️ {day_data.temperature_min:.1f}°C - {day_data.temperature_max:.1f}°C\n"
                    
                    if day_data.precipitation_sum and day_data.precipitation_sum > 0:
                        result += f"🌧️ Precipitación: {day_data.precipitation_sum:.1f}mm\n"
                    
                    if day_data.wind_speed_max:
                        result += f"🌬️ Viento máx: {day_data.wind_speed_max:.1f} km/h\n"
                    
                    result += "\n"
            
            result += f"📅 *Pronóstico generado: {forecast.generated_at.strftime('%H:%M')} - Fuente: Open-Meteo*"
            
            log_info(f"Pronóstico obtenido exitosamente para {location}")
            return result
            
        except Exception as e:
            log_error(f"Error en get_weather_forecast_tool: {e}")
            return f"❌ Error obteniendo pronóstico para '{location}'. Por favor intenta de nuevo."


@weather_agent.tool
async def get_weather_recommendations_tool(ctx: RunContext[WeatherContext], location: str) -> str:
    """Obtener recomendaciones basadas en las condiciones meteorológicas actuales."""
    
    location = sanitize_input(location)
    
    with WeatherOperationSpan("get_weather_recommendations", location):
        log_info(f"Obteniendo recomendaciones para: {location}")
        
        try:
            weather_service = WeatherService()
            response = await weather_service.get_weather_by_location(location)
            
            if not response or response.status == "error":
                return f"❌ No pude obtener datos para generar recomendaciones de '{location}'"
            
            current = response.current_weather
            recommendations = []
            
            # Recomendaciones por temperatura
            if current.temperature <= 0:
                recommendations.append("🧥 Usa ropa muy abrigada, gorro y guantes")
                recommendations.append("❄️ Cuidado con superficies heladas")
            elif current.temperature <= 10:
                recommendations.append("🧥 Lleva abrigo, hace frío")
            elif current.temperature <= 20:
                recommendations.append("👕 Ropa cómoda, temperatura agradable")
            elif current.temperature <= 30:
                recommendations.append("🌞 Ropa ligera y cómoda")
            else:
                recommendations.append("🥵 Ropa muy ligera, manténte hidratado")
                recommendations.append("☀️ Evita exposición prolongada al sol")
            
            # Recomendaciones por viento
            if current.wind_speed > 50:
                recommendations.append("💨 Viento muy fuerte, evita actividades al aire libre")
            elif current.wind_speed > 25:
                recommendations.append("🌬️ Viento moderado, asegura objetos sueltos")
            
            # Recomendaciones por precipitación
            if current.precipitation and current.precipitation > 0:
                recommendations.append("☔ Lleva paraguas o impermeable")
                if current.precipitation > 10:
                    recommendations.append("🌧️ Lluvia intensa, evita salir si es posible")
            
            # Recomendaciones por humedad
            if current.humidity > 80:
                recommendations.append("💧 Humedad alta, puede sentirse más caluroso")
            elif current.humidity < 30:
                recommendations.append("🏜️ Humedad baja, mantente hidratado")
            
            # Recomendaciones por condición
            if current.weather_condition in [WeatherCondition.THUNDERSTORM]:
                recommendations.append("⛈️ Tormenta eléctrica, busca refugio en interiores")
            elif current.weather_condition in [WeatherCondition.FOG]:
                recommendations.append("🌫️ Niebla, conduce con precaución")
            elif current.weather_condition in [WeatherCondition.SNOW]:
                recommendations.append("❄️ Nieve, ten cuidado al caminar y conducir")
            
            if not recommendations:
                recommendations.append("😊 Condiciones normales, disfruta del día")
            
            result = f"💡 **Recomendaciones para {response.location.name}:**\n\n"
            result += "\n".join(f"• {rec}" for rec in recommendations)
            
            log_info(f"Recomendaciones generadas para {location}")
            return result
            
        except Exception as e:
            log_error(f"Error en get_weather_recommendations_tool: {e}")
            return f"❌ Error generando recomendaciones para '{location}'"


# Funciones auxiliares

def get_condition_emoji(condition: Optional[WeatherCondition]) -> str:
    """Obtener emoji para la condición meteorológica."""
    
    if not condition:
        return "🌤️"
    
    emoji_map = {
        WeatherCondition.CLEAR: "☀️",
        WeatherCondition.PARTLY_CLOUDY: "⛅",
        WeatherCondition.CLOUDY: "☁️",
        WeatherCondition.OVERCAST: "☁️",
        WeatherCondition.FOG: "🌫️",
        WeatherCondition.DRIZZLE: "🌦️",
        WeatherCondition.RAIN: "🌧️",
        WeatherCondition.SNOW: "❄️",
        WeatherCondition.THUNDERSTORM: "⛈️",
        WeatherCondition.UNKNOWN: "🌤️"
    }
    
    return emoji_map.get(condition, "🌤️")


def get_wind_direction(degrees: Optional[float]) -> str:
    """Convertir grados a dirección del viento."""
    
    if degrees is None:
        return ""
    
    directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    
    index = round(degrees / 22.5) % 16
    return f"({directions[index]})"


def get_day_name(date_obj: date) -> str:
    """Obtener nombre del día en español."""
    
    days = {
        0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
        4: "Viernes", 5: "Sábado", 6: "Domingo"
    }
    
    today = date.today()
    if date_obj == today:
        return "Hoy"
    elif date_obj == today.replace(day=today.day + 1):
        return "Mañana"
    else:
        return days[date_obj.weekday()]


class ClimaAgent:
    """Wrapper de alto nivel para el agente del clima."""
    
    def __init__(self):
        self.agent = weather_agent
        self.weather_service = WeatherService()
        self.default_context = WeatherContext()
    
    async def process_query(self, user_input: str, context: Optional[WeatherContext] = None) -> str:
        """Procesar consulta del usuario."""
        
        if context is None:
            context = self.default_context
        
        user_input = sanitize_input(user_input)
        
        with WeatherOperationSpan("process_query"):
            log_info(f"Procesando consulta: {user_input[:100]}...")
            
            try:
                # Ejecutar agente
                result = await self.agent.run(user_input, deps=context)
                
                # Actualizar historial
                context.conversation_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_input": user_input,
                    "agent_response": result.data[:200] + "..." if len(result.data) > 200 else result.data
                })
                
                log_info("Consulta procesada exitosamente")
                return result.data
                
            except Exception as e:
                log_error(f"Error procesando consulta: {e}")
                return "❌ Lo siento, ocurrió un error procesando tu consulta. Por favor intenta de nuevo."
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Obtener estado del agente."""
        
        return {
            "status": "active",
            "model": get_settings().openai_model,
            "capabilities": [
                "current_weather",
                "weather_forecast", 
                "location_search",
                "weather_recommendations"
            ],
            "supported_languages": ["es"],
            "version": get_settings().version
        } 