#!/bin/bash
# =============================================================================
# CLIMA AGENT - Setup Simple para Ubuntu VM
# =============================================================================

set -e

echo "🚀 Configurando Clima Agent en Ubuntu VM..."

# Variables
PROJECT_DIR="/opt/clima"
SERVICE_USER="clima"
PYTHON_VERSION="3.11"

# 1. Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias
echo "🔧 Instalando dependencias..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    nginx \
    ufw

# 3. Crear usuario para el servicio
echo "👤 Creando usuario clima..."
sudo useradd -r -s /bin/false -d $PROJECT_DIR $SERVICE_USER || true

# 4. Configurar directorio del proyecto
echo "📁 Configurando directorio..."
sudo mkdir -p $PROJECT_DIR
sudo chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR

# 5. Clonar/copiar proyecto (asumiendo que ya está en /tmp/clima)
echo "📋 Copiando proyecto..."
sudo cp -r . $PROJECT_DIR/
sudo chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR

# 6. Crear entorno virtual
echo "🐍 Configurando Python..."
cd $PROJECT_DIR
sudo -u $SERVICE_USER python3 -m venv venv
sudo -u $SERVICE_USER ./venv/bin/pip install --upgrade pip
sudo -u $SERVICE_USER ./venv/bin/pip install -r requirements.txt

# 7. Configurar variables de entorno
echo "🔑 Configurando variables de entorno..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    sudo -u $SERVICE_USER cp env.example .env
    echo "⚠️  IMPORTANTE: Edita $PROJECT_DIR/.env con tus API keys"
fi

# 8. Crear servicio systemd
echo "⚙️  Creando servicio systemd..."
sudo tee /etc/systemd/system/clima-agent.service > /dev/null <<EOF
[Unit]
Description=Clima Weather Agent
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python main.py server --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 9. Configurar firewall básico
echo "🔥 Configurando firewall..."
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw --force enable

# 10. Habilitar y iniciar servicio
echo "🚀 Iniciando servicio..."
sudo systemctl daemon-reload
sudo systemctl enable clima-agent
sudo systemctl start clima-agent

# 11. Verificar estado
echo "✅ Verificando instalación..."
sleep 5
sudo systemctl status clima-agent --no-pager
echo ""
echo "🌐 Probando endpoint..."
curl -f http://localhost:8000/health || echo "❌ Error en health check"

echo ""
echo "🎉 ¡Instalación completada!"
echo ""
echo "📋 Comandos útiles:"
echo "   sudo systemctl status clima-agent    # Ver estado"
echo "   sudo systemctl restart clima-agent   # Reiniciar"
echo "   sudo journalctl -u clima-agent -f    # Ver logs"
echo "   curl http://$(hostname -I | awk '{print $1}'):8000/health  # Probar desde red"
echo ""
echo "🔧 Para configurar API keys:"
echo "   sudo nano $PROJECT_DIR/.env"
echo "   sudo systemctl restart clima-agent" 