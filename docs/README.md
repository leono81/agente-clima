# Weather Agent A2A API Documentation

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
curl -X POST http://localhost:8001/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_current_weather",
    "params": {"location": "Madrid"},
    "id": "weather-001"
  }'
```

### 3. Búsqueda de Ubicaciones

```bash
curl -X POST http://localhost:8001/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "search_locations",
    "params": {"query": "Barcelona", "limit": 3},
    "id": "search-001"
  }'
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

- **Solicitud**: `{"jsonrpc": "2.0", "method": "...", "params": {}, "id": "..."}`
- **Respuesta exitosa**: `{"jsonrpc": "2.0", "result": {}, "id": "..."}`
- **Respuesta de error**: `{"jsonrpc": "2.0", "error": {}, "id": "..."}`

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
