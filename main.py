#!/usr/bin/env python3
"""
Main - Punto de Entrada Principal del Clima Agent
================================================

Punto de entrada principal que permite ejecutar el agente del clima
en diferentes modos: CLI interactivo, servidor web, o comandos específicos.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import get_settings
from src.interfaces.cli import main as cli_main
from src.interfaces.server import run_server
from src.core.agent import ClimaAgent
from src.utils.logging import log_info, log_error


# Configuración de la aplicación principal
app = typer.Typer(
    name="clima-agent",
    help="🌤️ Agente Inteligente del Clima - Sistema Híbrido",
    rich_markup_mode="rich",
    no_args_is_help=True
)

console = Console()


@app.command("cli")
def run_cli():
    """
    🖥️ Ejecutar interfaz de línea de comandos.
    
    Inicia el modo CLI interactivo donde puedes chatear con el agente
    o usar comandos específicos para consultas meteorológicas.
    """
    
    console.print(Panel.fit(
        "[bold blue]🌤️ Iniciando Clima Agent CLI[/bold blue]\n\n"
        "[dim]Modo: Línea de comandos interactiva[/dim]",
        title="🚀 Iniciando",
        border_style="blue"
    ))
    
    try:
        cli_main()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]🛑 CLI interrumpido por el usuario[/bold yellow]")
    except Exception as e:
        log_error(f"Error en CLI: {e}")
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")


@app.command("server")
def run_web_server(
    host: Optional[str] = typer.Option(None, help="Host del servidor"),
    port: Optional[int] = typer.Option(None, help="Puerto del servidor"),
    debug: Optional[bool] = typer.Option(None, help="Modo debug")
):
    """
    🌐 Ejecutar servidor web con API REST + SSE + A2A.
    
    Inicia el servidor FastAPI que proporciona:
    - API REST para consultas meteorológicas
    - Server-Sent Events para streaming
    - Protocolo A2A para comunicación entre agentes
    - Interfaz web (si está configurada)
    """
    
    settings = get_settings()
    
    # Usar valores de configuración o argumentos
    server_host = host or settings.host
    server_port = port or settings.port
    debug_mode = debug if debug is not None else settings.debug
    
    console.print(Panel.fit(
        f"[bold green]🌐 Iniciando Servidor Web[/bold green]\n\n"
        f"[dim]Host: {server_host}[/dim]\n"
        f"[dim]Puerto: {server_port}[/dim]\n"
        f"[dim]Debug: {'✅ Activado' if debug_mode else '❌ Desactivado'}[/dim]\n"
        f"[dim]Documentación: http://{server_host}:{server_port}/docs[/dim]",
        title="🚀 Iniciando Servidor",
        border_style="green"
    ))
    
    try:
        # Actualizar configuración temporal
        if host:
            settings.host = host
        if port:
            settings.port = port
        if debug is not None:
            settings.debug = debug
        
        run_server()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]🛑 Servidor interrumpido por el usuario[/bold yellow]")
    except Exception as e:
        log_error(f"Error en servidor: {e}")
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")


@app.command("test")
def test_agent(
    query: str = typer.Argument("¿Cómo está el clima en Buenos Aires?", help="Consulta de prueba")
):
    """
    🧪 Probar el agente con una consulta específica.
    
    Útil para verificar que el agente funciona correctamente
    sin iniciar el modo interactivo.
    """
    
    console.print(Panel.fit(
        f"[bold cyan]🧪 Probando Agente[/bold cyan]\n\n"
        f"[dim]Consulta: {query}[/dim]",
        title="🔬 Modo Prueba",
        border_style="cyan"
    ))
    
    async def run_test():
        try:
            agent = ClimaAgent()
            
            console.print("\n[bold blue]🤖 Procesando consulta...[/bold blue]")
            response = await agent.process_query(query)
            
            console.print(Panel(
                response,
                title="🤖 Respuesta del Agente",
                border_style="green"
            ))
            
        except Exception as e:
            log_error(f"Error en prueba: {e}")
            console.print(Panel(
                f"❌ Error: {str(e)}",
                title="⚠️ Error en Prueba",
                border_style="red"
            ))
    
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]🛑 Prueba interrumpida[/bold yellow]")


@app.command("config")
def show_config():
    """
    ⚙️ Mostrar configuración actual del sistema.
    
    Muestra todas las configuraciones cargadas desde variables
    de entorno y archivos de configuración.
    """
    
    try:
        settings = get_settings()
        
        console.print(Panel.fit(
            f"[bold blue]⚙️ Configuración del Sistema[/bold blue]\n\n"
            f"[cyan]Proyecto:[/cyan] {settings.project_name}\n"
            f"[cyan]Versión:[/cyan] {settings.version}\n"
            f"[cyan]Descripción:[/cyan] {settings.description}\n\n"
            f"[yellow]Servidor:[/yellow]\n"
            f"  Host: {settings.host}\n"
            f"  Puerto: {settings.port}\n"
            f"  Debug: {'✅ Activado' if settings.debug else '❌ Desactivado'}\n\n"
            f"[yellow]OpenAI:[/yellow]\n"
            f"  Modelo: {settings.openai_model}\n"
            f"  API Key: {'✅ Configurada' if settings.openai_api_key else '❌ No configurada'}\n\n"
            f"[yellow]Logfire:[/yellow]\n"
            f"  Token: {'✅ Configurado' if settings.logfire_token else '❌ No configurado'}\n\n"
            f"[yellow]Directorios:[/yellow]\n"
            f"  Base: {settings.base_dir}\n"
            f"  Logs: {settings.logs_dir}",
            title="📋 Configuración",
            border_style="blue"
        ))
        
    except Exception as e:
        log_error(f"Error mostrando configuración: {e}")
        console.print(Panel(
            f"❌ Error obteniendo configuración: {str(e)}",
            title="⚠️ Error",
            border_style="red"
        ))


@app.command("version")
def show_version():
    """
    📋 Mostrar información de versión.
    """
    
    try:
        settings = get_settings()
        
        console.print(Panel.fit(
            f"[bold blue]🌤️ {settings.project_name}[/bold blue]\n\n"
            f"[cyan]Versión:[/cyan] {settings.version}\n"
            f"[cyan]Descripción:[/cyan] {settings.description}\n\n"
            f"[dim]Stack Tecnológico:[/dim]\n"
            f"• PydanticAI + OpenAI\n"
            f"• MCP Weather (Open-Meteo)\n"
            f"• Agent-to-Agent (A2A)\n"
            f"• FastAPI + SSE\n"
            f"• Pydantic Logfire",
            title="📋 Información de Versión",
            border_style="blue"
        ))
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")


@app.command("setup")
def setup_environment():
    """
    🔧 Configurar entorno inicial.
    
    Verifica dependencias y crea archivos de configuración necesarios.
    """
    
    console.print(Panel.fit(
        "[bold yellow]🔧 Configurando Entorno[/bold yellow]\n\n"
        "[dim]Verificando dependencias y configuración...[/dim]",
        title="⚙️ Setup",
        border_style="yellow"
    ))
    
    try:
        # Verificar archivo .env
        env_file = Path(".env")
        if not env_file.exists():
            console.print("[yellow]📝 Creando archivo .env desde plantilla...[/yellow]")
            
            example_file = Path("env.example")
            if example_file.exists():
                import shutil
                shutil.copy(example_file, env_file)
                console.print("[green]✅ Archivo .env creado[/green]")
            else:
                console.print("[red]❌ Archivo env.example no encontrado[/red]")
        else:
            console.print("[green]✅ Archivo .env existe[/green]")
        
        # Verificar directorio de logs
        settings = get_settings()
        if not settings.logs_dir.exists():
            settings.logs_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✅ Directorio de logs creado: {settings.logs_dir}[/green]")
        else:
            console.print(f"[green]✅ Directorio de logs existe: {settings.logs_dir}[/green]")
        
        # Verificar configuración OpenAI
        if not settings.openai_api_key:
            console.print("[yellow]⚠️ OpenAI API Key no configurada[/yellow]")
            console.print("[dim]Edita el archivo .env y agrega tu OPENAI_API_KEY[/dim]")
        else:
            console.print("[green]✅ OpenAI API Key configurada[/green]")
        
        console.print(Panel(
            "[green]🎉 Configuración completada[/green]\n\n"
            "[dim]Próximos pasos:[/dim]\n"
            "1. Edita .env con tu OpenAI API Key\n"
            "2. Ejecuta: python main.py test\n"
            "3. Inicia CLI: python main.py cli\n"
            "4. O servidor: python main.py server",
            title="✅ Setup Completo",
            border_style="green"
        ))
        
    except Exception as e:
        log_error(f"Error en setup: {e}")
        console.print(Panel(
            f"❌ Error durante setup: {str(e)}",
            title="⚠️ Error",
            border_style="red"
        ))


def main():
    """Punto de entrada principal."""
    
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]🛑 Operación cancelada[/bold yellow]")
    except Exception as e:
        log_error(f"Error en main: {e}")
        console.print(f"\n[bold red]❌ Error inesperado: {e}[/bold red]")


if __name__ == "__main__":
    main() 