# Weather Agent A2A - Production Dockerfile
# ========================================

FROM python:3.11-slim as builder

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .
COPY pyproject.toml .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Etapa de producción
FROM python:3.11-slim as production

# Crear usuario no-root
RUN groupadd -r weatheragent && useradd -r -g weatheragent weatheragent

# Instalar dependencias mínimas del sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorios
WORKDIR /app
RUN mkdir -p /app/logs /app/data && \
    chown -R weatheragent:weatheragent /app

# Copiar dependencias desde builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código de la aplicación
COPY --chown=weatheragent:weatheragent . .

# Cambiar a usuario no-root
USER weatheragent

# Variables de entorno
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV WEATHER_AGENT_HOST=0.0.0.0
ENV WEATHER_AGENT_PORT=8001
ENV WEATHER_AGENT_LOG_LEVEL=INFO
ENV WEATHER_AGENT_LOG_FORMAT=json

# Exponer puerto
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Comando por defecto
CMD ["python", "-m", "uvicorn", "src.a2a.server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"] 