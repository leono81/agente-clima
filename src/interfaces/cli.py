"""
CLI - Interfaz de Línea de Comandos
==================================

Interfaz CLI usando Typer y Rich para interactuar con el agente del clima
de manera atractiva desde la terminal.
"""

import asyncio
from typing import Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from src.core.agent import ClimaAgent, WeatherContext
from src.config.settings import get_settings
from src.utils.logging import log_info, log_error


# Configuración de la aplicación CLI
app = typer.Typer(
    name="clima-agent",
    help="🌤️ Agente Inteligente del Clima - Interfaz CLI",
    rich_markup_mode="rich",
    no_args_is_help=True
)

console = Console()


@app.command("chat")
def chat_interactive():
    """
    🗣️ Iniciar chat interactivo con el agente del clima.
    
    Modo conversacional donde puedes hacer preguntas sobre el clima
    y recibir respuestas en tiempo real.
    """
    
    console.print(Panel.fit(
        "[bold blue]🌤️ Clima Agent - Chat Interactivo[/bold blue]\n\n"
        "[dim]Escribe tus consultas sobre el clima y presiona Enter.[/dim]\n"
        "[dim]Comandos especiales:[/dim]\n"
        "[dim]• 'salir' - Terminar la sesión[/dim]\n"
        "[dim]• 'limpiar' - Limpiar pantalla[/dim]\n"
        "[dim]• 'estado' - Ver estado del agente[/dim]",
        title="🌍 Bienvenido",
        border_style="blue"
    ))
    
    # Crear contexto de sesión
    context = WeatherContext()
    agent = ClimaAgent()
    
    while True:
        try:
            # Prompt del usuario
            user_input = Prompt.ask(
                "\n[bold cyan]🤔 Tu consulta[/bold cyan]",
                default=""
            )
            
            if not user_input:
                continue
            
            # Comandos especiales
            if user_input.lower() in ["salir", "exit", "quit"]:
                console.print("\n[bold green]👋 ¡Hasta luego! Que tengas un buen día.[/bold green]")
                break
            
            elif user_input.lower() in ["limpiar", "clear"]:
                console.clear()
                continue
            
            elif user_input.lower() in ["estado", "status"]:
                asyncio.run(show_agent_status(agent))
                continue
            
            # Procesar consulta del agente
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("🤖 Procesando consulta...", total=None)
                
                try:
                    response = asyncio.run(agent.process_query(user_input, context))
                    
                    # Mostrar respuesta
                    console.print(Panel(
                        response,
                        title="🤖 Clima Agent",
                        border_style="green",
                        expand=False
                    ))
                    
                except Exception as e:
                    log_error(f"Error en chat CLI: {e}")
                    console.print(Panel(
                        f"❌ Error procesando la consulta: {str(e)}",
                        title="⚠️ Error",
                        border_style="red"
                    ))
        
        except KeyboardInterrupt:
            console.print("\n[bold yellow]🛑 Sesión interrumpida por el usuario[/bold yellow]")
            break
        except EOFError:
            console.print("\n[bold green]👋 Sesión terminada[/bold green]")
            break


@app.command("clima")
def get_weather(
    ubicacion: str = typer.Argument(..., help="Ubicación para consultar el clima"),
    formato: Optional[str] = typer.Option("completo", help="Formato de salida: completo, simple")
):
    """
    🌡️ Obtener clima actual para una ubicación específica.
    
    Ejemplos:
    clima-agent clima "Buenos Aires"
    clima-agent clima "Madrid, España" --formato simple
    """
    
    console.print(f"\n[bold blue]🔍 Consultando clima para:[/bold blue] {ubicacion}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("🌤️ Obteniendo datos meteorológicos...", total=None)
        
        try:
            agent = ClimaAgent()
            query = f"¿Cómo está el clima actual en {ubicacion}?"
            response = asyncio.run(agent.process_query(query))
            
            if formato == "simple":
                # Extraer información básica para formato simple
                lines = response.split('\n')
                simple_info = []
                for line in lines:
                    if any(emoji in line for emoji in ['🌡️', '💧', '🌬️']):
                        simple_info.append(line.strip())
                
                console.print("\n".join(simple_info))
            else:
                console.print(Panel(
                    response,
                    title=f"🌍 Clima en {ubicacion}",
                    border_style="blue"
                ))
        
        except Exception as e:
            log_error(f"Error obteniendo clima: {e}")
            console.print(Panel(
                f"❌ Error obteniendo el clima: {str(e)}",
                title="⚠️ Error",
                border_style="red"
            ))


@app.command("pronostico")
def get_forecast(
    ubicacion: str = typer.Argument(..., help="Ubicación para el pronóstico"),
    dias: int = typer.Option(7, help="Días de pronóstico (1-16)")
):
    """
    📅 Obtener pronóstico meteorológico para varios días.
    
    Ejemplos:
    clima-agent pronostico "Buenos Aires" --dias 5
    clima-agent pronostico "Barcelona"
    """
    
    dias = max(1, min(dias, 16))  # Limitar entre 1 y 16 días
    
    console.print(f"\n[bold blue]🔮 Pronóstico para:[/bold blue] {ubicacion} ({dias} días)")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("📊 Generando pronóstico...", total=None)
        
        try:
            agent = ClimaAgent()
            query = f"Dame el pronóstico del clima para {ubicacion} para los próximos {dias} días"
            response = asyncio.run(agent.process_query(query))
            
            console.print(Panel(
                response,
                title=f"📅 Pronóstico - {ubicacion}",
                border_style="green"
            ))
        
        except Exception as e:
            log_error(f"Error obteniendo pronóstico: {e}")
            console.print(Panel(
                f"❌ Error obteniendo pronóstico: {str(e)}",
                title="⚠️ Error",
                border_style="red"
            ))


@app.command("buscar")
def search_locations(
    consulta: str = typer.Argument(..., help="Términos de búsqueda para ubicaciones")
):
    """
    📍 Buscar ubicaciones geográficas.
    
    Útil cuando no estés seguro del nombre exacto de una ciudad.
    
    Ejemplos:
    clima-agent buscar "paris"
    clima-agent buscar "san"
    """
    
    console.print(f"\n[bold blue]🔍 Buscando ubicaciones:[/bold blue] {consulta}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("🗺️ Buscando ubicaciones...", total=None)
        
        try:
            agent = ClimaAgent()
            query = f"Busca ubicaciones que coincidan con '{consulta}'"
            response = asyncio.run(agent.process_query(query))
            
            console.print(Panel(
                response,
                title=f"📍 Resultados de búsqueda",
                border_style="yellow"
            ))
        
        except Exception as e:
            log_error(f"Error buscando ubicaciones: {e}")
            console.print(Panel(
                f"❌ Error en la búsqueda: {str(e)}",
                title="⚠️ Error",
                border_style="red"
            ))


@app.command("recomendaciones")
def get_recommendations(
    ubicacion: str = typer.Argument(..., help="Ubicación para recomendaciones")
):
    """
    💡 Obtener recomendaciones basadas en el clima actual.
    
    Incluye consejos sobre ropa, actividades y precauciones.
    
    Ejemplos:
    clima-agent recomendaciones "Buenos Aires"
    clima-agent recomendaciones "Miami"
    """
    
    console.print(f"\n[bold blue]💡 Recomendaciones para:[/bold blue] {ubicacion}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("🎯 Generando recomendaciones...", total=None)
        
        try:
            agent = ClimaAgent()
            query = f"Dame recomendaciones basadas en el clima actual de {ubicacion}"
            response = asyncio.run(agent.process_query(query))
            
            console.print(Panel(
                response,
                title=f"💡 Recomendaciones - {ubicacion}",
                border_style="magenta"
            ))
        
        except Exception as e:
            log_error(f"Error obteniendo recomendaciones: {e}")
            console.print(Panel(
                f"❌ Error obteniendo recomendaciones: {str(e)}",
                title="⚠️ Error",
                border_style="red"
            ))


@app.command("estado")
def show_status():
    """
    📊 Mostrar estado del agente y configuración del sistema.
    """
    
    console.print("\n[bold blue]📊 Estado del Sistema[/bold blue]")
    
    try:
        agent = ClimaAgent()
        asyncio.run(show_agent_status(agent))
    except Exception as e:
        log_error(f"Error mostrando estado: {e}")
        console.print(Panel(
            f"❌ Error obteniendo estado: {str(e)}",
            title="⚠️ Error",
            border_style="red"
        ))


async def show_agent_status(agent: ClimaAgent):
    """Mostrar estado detallado del agente."""
    
    try:
        status = await agent.get_agent_status()
        settings = get_settings()
        
        # Tabla de configuración
        config_table = Table(title="⚙️ Configuración", box=box.ROUNDED)
        config_table.add_column("Parámetro", style="cyan")
        config_table.add_column("Valor", style="green")
        
        config_table.add_row("Proyecto", settings.project_name)
        config_table.add_row("Versión", settings.version)
        config_table.add_row("Modelo OpenAI", settings.openai_model)
        config_table.add_row("Servidor", f"{settings.host}:{settings.port}")
        config_table.add_row("Modo Debug", "✅ Activado" if settings.debug else "❌ Desactivado")
        
        # Tabla de capacidades
        capabilities_table = Table(title="🛠️ Capacidades", box=box.ROUNDED)
        capabilities_table.add_column("Capacidad", style="yellow")
        capabilities_table.add_column("Estado", style="green")
        
        for capability in status.get("capabilities", []):
            capabilities_table.add_row(capability, "✅ Disponible")
        
        console.print(config_table)
        console.print(capabilities_table)
        
        # Estado general
        console.print(Panel(
            f"[green]✅ Sistema operativo[/green]\n"
            f"[dim]Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
            title="🟢 Estado General",
            border_style="green"
        ))
        
    except Exception as e:
        log_error(f"Error en show_agent_status: {e}")
        console.print(Panel(
            f"❌ Error obteniendo estado del agente: {str(e)}",
            title="⚠️ Error",
            border_style="red"
        ))


@app.command("version")
def show_version():
    """
    📋 Mostrar información de versión del agente.
    """
    
    settings = get_settings()
    
    version_info = Text()
    version_info.append("🌤️ ", style="blue")
    version_info.append(settings.project_name, style="bold blue")
    version_info.append(f" v{settings.version}\n", style="blue")
    version_info.append(settings.description, style="dim")
    
    console.print(Panel(
        version_info,
        title="📋 Información de Versión",
        border_style="blue"
    ))


def main():
    """Punto de entrada principal para la CLI."""
    
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]🛑 Operación cancelada por el usuario[/bold yellow]")
    except Exception as e:
        log_error(f"Error en CLI principal: {e}")
        console.print(Panel(
            f"❌ Error inesperado: {str(e)}",
            title="⚠️ Error Fatal",
            border_style="red"
        ))


if __name__ == "__main__":
    main() 