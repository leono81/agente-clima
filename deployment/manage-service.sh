#!/bin/bash
# =============================================================================
# CLIMA AGENT - Gestión del Servicio
# =============================================================================

SERVICE_NAME="clima-agent"
PROJECT_DIR="/opt/clima"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo "🌤️  Clima Agent - Gestión del Servicio"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start     - Iniciar el servicio"
    echo "  stop      - Detener el servicio"
    echo "  restart   - Reiniciar el servicio"
    echo "  status    - Ver estado del servicio"
    echo "  logs      - Ver logs en tiempo real"
    echo "  health    - Verificar salud del servicio"
    echo "  config    - Editar configuración (.env)"
    echo "  update    - Actualizar dependencias"
    echo "  backup    - Crear backup de configuración"
    echo "  help      - Mostrar esta ayuda"
}

check_service_exists() {
    if ! systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
        echo -e "${RED}❌ El servicio $SERVICE_NAME no está instalado${NC}"
        echo "Ejecuta primero: ./deployment/simple-setup.sh"
        exit 1
    fi
}

start_service() {
    echo -e "${BLUE}🚀 Iniciando $SERVICE_NAME...${NC}"
    sudo systemctl start $SERVICE_NAME
    sleep 2
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}✅ Servicio iniciado correctamente${NC}"
    else
        echo -e "${RED}❌ Error al iniciar el servicio${NC}"
        sudo systemctl status $SERVICE_NAME --no-pager
    fi
}

stop_service() {
    echo -e "${YELLOW}⏹️  Deteniendo $SERVICE_NAME...${NC}"
    sudo systemctl stop $SERVICE_NAME
    echo -e "${GREEN}✅ Servicio detenido${NC}"
}

restart_service() {
    echo -e "${BLUE}🔄 Reiniciando $SERVICE_NAME...${NC}"
    sudo systemctl restart $SERVICE_NAME
    sleep 2
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}✅ Servicio reiniciado correctamente${NC}"
    else
        echo -e "${RED}❌ Error al reiniciar el servicio${NC}"
        sudo systemctl status $SERVICE_NAME --no-pager
    fi
}

show_status() {
    echo -e "${BLUE}📊 Estado del servicio:${NC}"
    sudo systemctl status $SERVICE_NAME --no-pager
    echo ""
    echo -e "${BLUE}🔗 Información de red:${NC}"
    local ip=$(hostname -I | awk '{print $1}')
    echo "URL local: http://localhost:8000"
    echo "URL red: http://$ip:8000"
}

show_logs() {
    echo -e "${BLUE}📋 Logs en tiempo real (Ctrl+C para salir):${NC}"
    sudo journalctl -u $SERVICE_NAME -f --no-pager
}

check_health() {
    echo -e "${BLUE}🏥 Verificando salud del servicio...${NC}"
    local ip=$(hostname -I | awk '{print $1}')
    
    # Verificar si el servicio está corriendo
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}✅ Servicio activo${NC}"
    else
        echo -e "${RED}❌ Servicio inactivo${NC}"
        return 1
    fi
    
    # Verificar endpoint de salud
    if curl -f -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ Endpoint de salud responde${NC}"
        echo "🌐 Accesible en: http://$ip:8000"
    else
        echo -e "${RED}❌ Endpoint de salud no responde${NC}"
        echo "Revisa los logs: $0 logs"
    fi
}

edit_config() {
    echo -e "${BLUE}⚙️  Editando configuración...${NC}"
    if [ -f "$PROJECT_DIR/.env" ]; then
        sudo nano "$PROJECT_DIR/.env"
        echo -e "${YELLOW}🔄 Reinicia el servicio para aplicar cambios: $0 restart${NC}"
    else
        echo -e "${RED}❌ Archivo .env no encontrado en $PROJECT_DIR${NC}"
    fi
}

update_dependencies() {
    echo -e "${BLUE}📦 Actualizando dependencias...${NC}"
    sudo systemctl stop $SERVICE_NAME
    cd $PROJECT_DIR
    sudo -u clima ./venv/bin/pip install --upgrade -r requirements.txt
    sudo systemctl start $SERVICE_NAME
    echo -e "${GREEN}✅ Dependencias actualizadas${NC}"
}

backup_config() {
    local backup_dir="$HOME/clima-backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/clima-config-$timestamp.tar.gz"
    
    echo -e "${BLUE}💾 Creando backup...${NC}"
    mkdir -p "$backup_dir"
    
    sudo tar -czf "$backup_file" -C "$PROJECT_DIR" .env logs/ || true
    
    if [ -f "$backup_file" ]; then
        echo -e "${GREEN}✅ Backup creado: $backup_file${NC}"
    else
        echo -e "${RED}❌ Error creando backup${NC}"
    fi
}

# Función principal
main() {
    case "${1:-help}" in
        start)
            check_service_exists
            start_service
            ;;
        stop)
            check_service_exists
            stop_service
            ;;
        restart)
            check_service_exists
            restart_service
            ;;
        status)
            check_service_exists
            show_status
            ;;
        logs)
            check_service_exists
            show_logs
            ;;
        health)
            check_service_exists
            check_health
            ;;
        config)
            edit_config
            ;;
        update)
            check_service_exists
            update_dependencies
            ;;
        backup)
            backup_config
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ Comando desconocido: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@" 