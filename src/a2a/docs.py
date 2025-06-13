#!/usr/bin/env python3
"""
A2A Documentation Generator
===========================

Generador automático de documentación para APIs A2A.
Incluye OpenAPI/Swagger, ejemplos de uso y especificaciones completas.
"""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
import json
import yaml


class A2ADocumentationGenerator:
    """Generador de documentación A2A."""
    
    def __init__(self, app: FastAPI, agent_id: str = "weather-agent-001"):
        self.app = app
        self.agent_id = agent_id
    
    def generate_openapi_schema(self) -> Dict[str, Any]:
        """Generar esquema OpenAPI completo."""
        
        # Configuración base OpenAPI
        openapi_schema = get_openapi(
            title="Weather Agent A2A API",
            version="1.0.0",
            description=self._get_api_description(),
            routes=self.app.routes,
        )
        
        # Agregar información adicional A2A
        openapi_schema["info"]["contact"] = {
            "name": "Weather Agent Support",
            "email": "support@weather-agent.com",
            "url": "https://weather-agent.com/support"
        }
        
        openapi_schema["info"]["license"] = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
        
        # Agregar servidores
        openapi_schema["servers"] = [
            {
                "url": "http://localhost:8001",
                "description": "Development server"
            },
            {
                "url": "https://api.weather-agent.com",
                "description": "Production server"
            }
        ]
        
        # Agregar tags para organización
        openapi_schema["tags"] = [
            {
                "name": "Agent Discovery",
                "description": "Endpoints para descubrimiento de agentes A2A"
            },
            {
                "name": "Health & Status",
                "description": "Endpoints de salud y estado del agente"
            },
            {
                "name": "JSON-RPC",
                "description": "Comunicación JSON-RPC 2.0 entre agentes"
            },
            {
                "name": "Task Management",
                "description": "Gestión de tareas asíncronas"
            },
            {
                "name": "Weather Capabilities",
                "description": "Capacidades meteorológicas del agente"
            }
        ]
        
        # Agregar ejemplos de JSON-RPC
        openapi_schema["components"]["examples"] = self._get_jsonrpc_examples()
        
        # Agregar esquemas personalizados
        openapi_schema["components"]["schemas"].update(self._get_custom_schemas())
        
        return openapi_schema
    
    def _get_api_description(self) -> str:
        """Obtener descripción detallada de la API."""
        return """
# Weather Agent A2A API

API completa para comunicación Agent-to-Agent (A2A) del agente meteorológico.

## Características

- **JSON-RPC 2.0**: Protocolo estándar para comunicación entre agentes
- **Agent Discovery**: Descubrimiento automático mediante Agent Card
- **Capacidades Meteorológicas**: Clima actual, pronósticos y búsqueda de ubicaciones
- **Gestión de Tareas**: Ejecución asíncrona de operaciones complejas
- **Monitoreo**: Health checks y métricas de rendimiento

## Flujo de Comunicación A2A

1. **Descubrimiento**: GET `/.well-known/agent.json`
2. **Capacidades**: POST `/rpc` con método `get_capabilities`
3. **Ejecución**: POST `/rpc` con capacidades específicas
4. **Monitoreo**: GET `/health` y `/status`

## Autenticación

Actualmente no se requiere autenticación. En producción se recomienda:
- API Keys para agentes registrados
- OAuth 2.0 para aplicaciones cliente
- mTLS para comunicación segura entre agentes

## Rate Limiting

- **Desarrollo**: Sin límites
- **Producción**: 100 requests/minuto por agente
        """
    
    def _get_jsonrpc_examples(self) -> Dict[str, Any]:
        """Obtener ejemplos de JSON-RPC."""
        return {
            "get_current_weather_request": {
                "summary": "Solicitud de clima actual",
                "value": {
                    "jsonrpc": "2.0",
                    "method": "get_current_weather",
                    "params": {
                        "location": "Madrid"
                    },
                    "id": "weather-001"
                }
            },
            "get_current_weather_response": {
                "summary": "Respuesta de clima actual",
                "value": {
                    "jsonrpc": "2.0",
                    "result": {
                        "status": "success",
                        "location": {
                            "name": "Madrid",
                            "latitude": 40.4165,
                            "longitude": -3.70256,
                            "country": "España"
                        },
                        "current_weather": {
                            "temperature": 24.0,
                            "humidity": 65.0,
                            "weather_condition": "partly_cloudy",
                            "timestamp": "2025-06-13T22:00:00Z"
                        }
                    },
                    "id": "weather-001"
                }
            },
            "search_locations_request": {
                "summary": "Solicitud de búsqueda de ubicaciones",
                "value": {
                    "jsonrpc": "2.0",
                    "method": "search_locations",
                    "params": {
                        "query": "Barcelona",
                        "limit": 3
                    },
                    "id": "search-001"
                }
            },
            "submit_task_request": {
                "summary": "Envío de tarea asíncrona",
                "value": {
                    "jsonrpc": "2.0",
                    "method": "submit_task",
                    "params": {
                        "capability": "get_current_weather",
                        "input_data": {
                            "location": "Tokyo"
                        }
                    },
                    "id": "task-001"
                }
            },
            "error_response": {
                "summary": "Respuesta de error JSON-RPC",
                "value": {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": "Error interno del servidor",
                        "data": {
                            "details": "No se encontró la ubicación especificada"
                        }
                    },
                    "id": "weather-001"
                }
            }
        }
    
    def _get_custom_schemas(self) -> Dict[str, Any]:
        """Obtener esquemas personalizados."""
        return {
            "AgentCard": {
                "type": "object",
                "properties": {
                    "agent": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "version": {"type": "string"},
                            "description": {"type": "string"},
                            "capabilities": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Capability"}
                            }
                        }
                    }
                }
            },
            "Capability": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "input_schema": {"type": "object"},
                    "output_schema": {"type": "object"},
                    "examples": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                }
            },
            "JSONRPCRequest": {
                "type": "object",
                "required": ["jsonrpc", "method"],
                "properties": {
                    "jsonrpc": {
                        "type": "string",
                        "enum": ["2.0"]
                    },
                    "method": {"type": "string"},
                    "params": {"type": "object"},
                    "id": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "number"},
                            {"type": "null"}
                        ]
                    }
                }
            },
            "JSONRPCResponse": {
                "type": "object",
                "required": ["jsonrpc"],
                "properties": {
                    "jsonrpc": {
                        "type": "string",
                        "enum": ["2.0"]
                    },
                    "result": {"type": "object"},
                    "error": {"$ref": "#/components/schemas/JSONRPCError"},
                    "id": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "number"},
                            {"type": "null"}
                        ]
                    }
                }
            },
            "JSONRPCError": {
                "type": "object",
                "required": ["code", "message"],
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": {"type": "object"}
                }
            },
            "WeatherData": {
                "type": "object",
                "properties": {
                    "temperature": {"type": "number"},
                    "humidity": {"type": "number"},
                    "pressure": {"type": "number"},
                    "wind_speed": {"type": "number"},
                    "weather_condition": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "Location": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                    "country": {"type": "string"},
                    "region": {"type": "string"}
                }
            }
        }
    
    def generate_usage_examples(self) -> Dict[str, Any]:
        """Generar ejemplos de uso completos."""
        return {
            "basic_weather_query": {
                "title": "Consulta Básica de Clima",
                "description": "Ejemplo de consulta simple de clima actual",
                "steps": [
                    {
                        "step": 1,
                        "description": "Descubrir agente",
                        "request": {
                            "method": "GET",
                            "url": "/.well-known/agent.json"
                        }
                    },
                    {
                        "step": 2,
                        "description": "Obtener clima actual",
                        "request": {
                            "method": "POST",
                            "url": "/rpc",
                            "body": {
                                "jsonrpc": "2.0",
                                "method": "get_current_weather",
                                "params": {"location": "Madrid"},
                                "id": "weather-001"
                            }
                        }
                    }
                ]
            },
            "multi_city_comparison": {
                "title": "Comparación Multi-Ciudad",
                "description": "Comparar clima de múltiples ciudades",
                "steps": [
                    {
                        "step": 1,
                        "description": "Consultas paralelas",
                        "requests": [
                            {
                                "method": "POST",
                                "url": "/rpc",
                                "body": {
                                    "jsonrpc": "2.0",
                                    "method": "get_current_weather",
                                    "params": {"location": "Madrid"},
                                    "id": "madrid-001"
                                }
                            },
                            {
                                "method": "POST",
                                "url": "/rpc",
                                "body": {
                                    "jsonrpc": "2.0",
                                    "method": "get_current_weather",
                                    "params": {"location": "Barcelona"},
                                    "id": "barcelona-001"
                                }
                            }
                        ]
                    }
                ]
            },
            "async_task_workflow": {
                "title": "Flujo de Tareas Asíncronas",
                "description": "Gestión de tareas de larga duración",
                "steps": [
                    {
                        "step": 1,
                        "description": "Enviar tarea",
                        "request": {
                            "method": "POST",
                            "url": "/rpc",
                            "body": {
                                "jsonrpc": "2.0",
                                "method": "submit_task",
                                "params": {
                                    "capability": "get_forecast",
                                    "input_data": {"location": "Tokyo", "days": 7}
                                },
                                "id": "task-001"
                            }
                        }
                    },
                    {
                        "step": 2,
                        "description": "Monitorear progreso",
                        "request": {
                            "method": "POST",
                            "url": "/rpc",
                            "body": {
                                "jsonrpc": "2.0",
                                "method": "get_task_status",
                                "params": {"task_id": "task-uuid-here"},
                                "id": "status-001"
                            }
                        }
                    }
                ]
            }
        }
    
    def generate_integration_guide(self) -> Dict[str, Any]:
        """Generar guía de integración."""
        return {
            "title": "Guía de Integración A2A",
            "sections": [
                {
                    "title": "Configuración Inicial",
                    "content": [
                        "1. Configurar endpoint del agente meteorológico",
                        "2. Implementar cliente JSON-RPC 2.0",
                        "3. Configurar manejo de errores y timeouts",
                        "4. Implementar cache para ubicaciones frecuentes"
                    ]
                },
                {
                    "title": "Flujo de Descubrimiento",
                    "content": [
                        "1. GET /.well-known/agent.json para obtener capacidades",
                        "2. Validar versión del protocolo A2A",
                        "3. Verificar capacidades requeridas",
                        "4. Configurar endpoints de comunicación"
                    ]
                },
                {
                    "title": "Mejores Prácticas",
                    "content": [
                        "- Implementar retry con backoff exponencial",
                        "- Usar connection pooling para mejor rendimiento",
                        "- Cachear respuestas de ubicaciones por 1 hora",
                        "- Implementar circuit breaker para resiliencia",
                        "- Monitorear métricas de latencia y errores"
                    ]
                },
                {
                    "title": "Manejo de Errores",
                    "content": [
                        "- Código -32700: Error de parsing JSON",
                        "- Código -32600: Solicitud inválida",
                        "- Código -32601: Método no encontrado",
                        "- Código -32602: Parámetros inválidos",
                        "- Código -32603: Error interno del servidor"
                    ]
                }
            ]
        }
    
    def save_documentation(self, output_dir: str = "docs/"):
        """Guardar toda la documentación generada."""
        import os
        
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Generar y guardar OpenAPI schema
        openapi_schema = self.generate_openapi_schema()
        
        with open(f"{output_dir}/openapi.json", "w") as f:
            json.dump(openapi_schema, f, indent=2)
        
        with open(f"{output_dir}/openapi.yaml", "w") as f:
            yaml.dump(openapi_schema, f, default_flow_style=False)
        
        # Generar y guardar ejemplos de uso
        usage_examples = self.generate_usage_examples()
        
        with open(f"{output_dir}/usage_examples.json", "w") as f:
            json.dump(usage_examples, f, indent=2)
        
        # Generar y guardar guía de integración
        integration_guide = self.generate_integration_guide()
        
        with open(f"{output_dir}/integration_guide.json", "w") as f:
            json.dump(integration_guide, f, indent=2)
        
        # Generar README.md
        self._generate_readme(output_dir)
        
        print(f"📚 Documentación generada en: {output_dir}")
        print(f"   - OpenAPI: {output_dir}/openapi.json")
        print(f"   - Ejemplos: {output_dir}/usage_examples.json")
        print(f"   - Guía: {output_dir}/integration_guide.json")
        print(f"   - README: {output_dir}/README.md")
    
    def _generate_readme(self, output_dir: str):
        """Generar README.md completo."""
        readme_content = f"""# Weather Agent A2A API Documentation

## Descripción

API completa para comunicación Agent-to-Agent (A2A) del agente meteorológico.

## Archivos de Documentación

- **`openapi.json`**: Especificación OpenAPI 3.0 completa
- **`openapi.yaml`**: Especificación OpenAPI en formato YAML
- **`usage_examples.json`**: Ejemplos de uso y casos comunes
- **`integration_guide.json`**: Guía detallada de integración

## Inicio Rápido

### 1. Descubrimiento del Agente

```bash
curl http://localhost:8001/.well-known/agent.json
```

### 2. Consulta de Clima

```bash
curl -X POST http://localhost:8001/rpc \\
  -H "Content-Type: application/json" \\
  -d '{{
    "jsonrpc": "2.0",
    "method": "get_current_weather",
    "params": {{"location": "Madrid"}},
    "id": "weather-001"
  }}'
```

### 3. Búsqueda de Ubicaciones

```bash
curl -X POST http://localhost:8001/rpc \\
  -H "Content-Type: application/json" \\
  -d '{{
    "jsonrpc": "2.0",
    "method": "search_locations",
    "params": {{"query": "Barcelona", "limit": 3}},
    "id": "search-001"
  }}'
```

## Capacidades Disponibles

- **`get_current_weather`**: Obtener clima actual de una ubicación
- **`get_forecast`**: Obtener pronóstico meteorológico (próximamente)
- **`search_locations`**: Buscar ubicaciones por nombre
- **`get_agent_info`**: Información del agente
- **`get_capabilities`**: Lista de capacidades disponibles
- **`submit_task`**: Enviar tarea asíncrona
- **`get_task_status`**: Obtener estado de tarea

## Endpoints de Monitoreo

- **`GET /health`**: Health check del agente
- **`GET /status`**: Estado detallado del agente
- **`GET /tasks`**: Lista de tareas activas

## Especificación JSON-RPC 2.0

Todas las comunicaciones siguen el estándar JSON-RPC 2.0:

- **Solicitud**: `{{"jsonrpc": "2.0", "method": "...", "params": {{}}, "id": "..."}}`
- **Respuesta exitosa**: `{{"jsonrpc": "2.0", "result": {{}}, "id": "..."}}`
- **Respuesta de error**: `{{"jsonrpc": "2.0", "error": {{}}, "id": "..."}}`

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| -32700 | Error de parsing JSON |
| -32600 | Solicitud inválida |
| -32601 | Método no encontrado |
| -32602 | Parámetros inválidos |
| -32603 | Error interno del servidor |

## Visualización con Swagger UI

Para visualizar la documentación interactiva:

1. Instalar swagger-ui-express (Node.js) o equivalente
2. Servir el archivo `openapi.json`
3. Acceder a la interfaz web

## Soporte

- **Email**: support@weather-agent.com
- **Documentación**: https://weather-agent.com/docs
- **GitHub**: https://github.com/weather-agent/a2a-api

---

Generado automáticamente por A2A Documentation Generator v1.0.0
"""
        
        with open(f"{output_dir}/README.md", "w") as f:
            f.write(readme_content)


def generate_complete_documentation(app: FastAPI, agent_id: str = "weather-agent-001"):
    """Función helper para generar documentación completa."""
    doc_generator = A2ADocumentationGenerator(app, agent_id)
    doc_generator.save_documentation()
    return doc_generator 