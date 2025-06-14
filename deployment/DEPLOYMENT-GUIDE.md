# 🚀 Guía de Deployment - Ubuntu VM con Systemd

## 📋 Pre-requisitos
- Ubuntu VM en Proxmox
- Acceso SSH a la VM
- Usuario con permisos sudo

## ⚡ Instalación Rápida

### 1. Subir el proyecto a la VM
```bash
# Desde tu máquina local
scp -r clima/ usuario@ip-vm:/tmp/

# O clonar directamente en la VM
ssh usuario@ip-vm
git clone <tu-repo> /tmp/clima
```

### 2. Ejecutar instalación automática
```bash
cd /tmp/clima
chmod +x deployment/simple-setup.sh
./deployment/simple-setup.sh
```

### 3. Configurar API Keys
```bash
sudo nano /opt/clima/.env
# Editar las siguientes variables:
# OPENAI_API_KEY=tu_api_key_aqui
# WEATHER_API_KEY=tu_weather_key_aqui (si aplica)
```

### 4. Reiniciar servicio
```bash
sudo systemctl restart clima-agent
```

### 5. Verificar funcionamiento
```bash
curl http://localhost:8000/health
```

## 🛠️ Gestión del Servicio

### Usar el script de gestión
```bash
# Hacer ejecutable
chmod +x deployment/manage-service.sh

# Ver ayuda
./deployment/manage-service.sh help

# Comandos principales
./deployment/manage-service.sh status    # Ver estado
./deployment/manage-service.sh logs      # Ver logs
./deployment/manage-service.sh restart   # Reiniciar
./deployment/manage-service.sh health    # Verificar salud
./deployment/manage-service.sh config    # Editar configuración
```

### Comandos systemd directos
```bash
# Estado del servicio
sudo systemctl status clima-agent

# Iniciar/parar/reiniciar
sudo systemctl start clima-agent
sudo systemctl stop clima-agent
sudo systemctl restart clima-agent

# Ver logs
sudo journalctl -u clima-agent -f

# Habilitar/deshabilitar autostart
sudo systemctl enable clima-agent
sudo systemctl disable clima-agent
```

## 🌐 Acceso desde la Red

### Obtener IP de la VM
```bash
hostname -I
# Ejemplo: 192.168.1.100
```

### Probar desde otros dispositivos
```bash
curl http://192.168.1.100:8000/health
```

### Configurar firewall (si es necesario)
```bash
# El script ya configura UFW, pero si necesitas ajustar:
sudo ufw allow from 192.168.1.0/24 to any port 8000
sudo ufw reload
```

## 🔧 Configuración de Proxmox

### Para acceso desde fuera de la red local
1. En Proxmox, ir a la VM → Hardware → Network Device
2. Si usas NAT, configurar port forwarding
3. Si usas Bridge, la VM tendrá IP directa en tu LAN

### Port forwarding (si usas NAT)
```bash
# En el host Proxmox (si es necesario)
iptables -t nat -A PREROUTING -p tcp --dport 8000 -j DNAT --to-destination IP_VM:8000
```

## 📊 Monitoreo Básico

### Ver uso de recursos
```bash
# CPU y memoria del proceso
ps aux | grep clima
top -p $(pgrep -f clima)

# Uso de puerto
netstat -tlnp | grep 8000
ss -tlnp | grep 8000
```

### Logs importantes
```bash
# Logs del servicio
sudo journalctl -u clima-agent --since "1 hour ago"

# Logs del sistema
sudo tail -f /var/log/syslog | grep clima
```

## 🚨 Troubleshooting

### El servicio no inicia
```bash
# Ver error específico
sudo systemctl status clima-agent -l

# Ver logs detallados
sudo journalctl -u clima-agent -n 50

# Verificar permisos
ls -la /opt/clima/
sudo -u clima /opt/clima/venv/bin/python --version
```

### Puerto ocupado
```bash
# Ver qué usa el puerto 8000
sudo lsof -i :8000
sudo netstat -tlnp | grep 8000

# Cambiar puerto (editar servicio)
sudo systemctl edit clima-agent
# Agregar:
# [Service]
# ExecStart=
# ExecStart=/opt/clima/venv/bin/python main.py server --host 0.0.0.0 --port 8001
```

### Problemas de dependencias
```bash
# Reinstalar dependencias
cd /opt/clima
sudo -u clima ./venv/bin/pip install --force-reinstall -r requirements.txt
sudo systemctl restart clima-agent
```

## 📦 Actualización del Código

### Actualizar desde git
```bash
cd /opt/clima
sudo systemctl stop clima-agent
sudo -u clima git pull
sudo -u clima ./venv/bin/pip install -r requirements.txt
sudo systemctl start clima-agent
```

### Backup antes de actualizar
```bash
./deployment/manage-service.sh backup
```

## 🔒 Seguridad Básica

### Configuración UFW aplicada
```bash
sudo ufw status
# Debería mostrar:
# 22/tcp (SSH)
# 8000/tcp (Clima Agent)
```

### Cambiar usuario del servicio (opcional)
```bash
# Si quieres usar otro usuario
sudo systemctl stop clima-agent
sudo useradd -r -s /bin/false mi-usuario
sudo chown -R mi-usuario:mi-usuario /opt/clima
# Editar /etc/systemd/system/clima-agent.service
# Cambiar User= y Group=
sudo systemctl daemon-reload
sudo systemctl start clima-agent
```

## 📈 Optimización para VM Pequeña

### Reducir uso de memoria
```bash
# En /opt/clima/.env agregar:
WORKERS=1
MAX_CONNECTIONS=10
CACHE_SIZE=100

# Reiniciar servicio
sudo systemctl restart clima-agent
```

### Limpiar logs periódicamente
```bash
# Configurar logrotate
sudo nano /etc/logrotate.d/clima-agent
# Contenido:
# /opt/clima/logs/*.log {
#     daily
#     rotate 7
#     compress
#     missingok
#     notifempty
#     create 644 clima clima
# }
```

## ✅ Verificación Final

### Checklist de funcionamiento
- [ ] Servicio activo: `sudo systemctl is-active clima-agent`
- [ ] Puerto abierto: `curl http://localhost:8000/health`
- [ ] Acceso desde red: `curl http://IP_VM:8000/health`
- [ ] Logs sin errores: `sudo journalctl -u clima-agent -n 20`
- [ ] Autostart habilitado: `sudo systemctl is-enabled clima-agent`

¡Tu agente está listo para funcionar 24/7 en tu VM! 🎉 