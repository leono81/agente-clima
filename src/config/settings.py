"""
Settings - Configuración General del Sistema
============================================

Configuración centralizada usando Pydantic Settings para validación
y carga desde variables de entorno.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración principal del Clima Agent."""
    
    # Project Info
    project_name: str = "Clima Agent"
    version: str = "1.0.0"
    description: str = "Agente Híbrido del Clima con PydanticAI + MCP + A2A"
    
    # Environment Configuration
    environment: str = Field(default="development", description="Entorno de ejecución")
    log_level: str = Field(default="INFO", description="Nivel de logging")
    workers: int = Field(default=1, description="Número de workers")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4o-mini", description="Modelo OpenAI a usar")
    
    # Logfire Configuration
    logfire_token: Optional[str] = Field(default=None, description="Token de Logfire para observabilidad")
    
    # Server Configuration
    host: str = Field(default="localhost", description="Host del servidor")
    port: int = Field(default=7777, description="Puerto del servidor")
    server_name: str = Field(default="Clima Agent", description="Nombre del servidor")
    debug: bool = Field(default=False, description="Modo debug")
    
    # MCP Weather Configuration
    weather_mcp_url: str = Field(default="http://localhost:8000", description="URL del servidor MCP Weather")
    weather_api_timeout: int = Field(default=30, description="Timeout para APIs del clima")
    
    # A2A Configuration
    a2a_agent_id: str = Field(default="clima-agent", description="ID del agente A2A")
    a2a_secret_key: Optional[str] = Field(default=None, description="Clave secreta A2A")
    
    # Agent UI Configuration
    agent_ui_url: str = Field(default="http://localhost:3000", description="URL de Agent UI")
    enable_cors: bool = Field(default=True, description="Habilitar CORS")
    
    # Security
    api_secret_key: str = Field(default="default-secret-key", description="Clave secreta de la API")
    ssl_enabled: bool = Field(default=False, description="SSL habilitado")
    
    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Crear directorio de logs si no existe
        self.logs_dir.mkdir(exist_ok=True)


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """Obtener la configuración global."""
    return settings


def reload_settings() -> Settings:
    """Recargar la configuración."""
    global settings
    settings = Settings()
    return settings 