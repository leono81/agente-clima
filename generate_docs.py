#!/usr/bin/env python3
"""
Script para generar documentación automática A2A
===============================================

Genera documentación completa incluyendo OpenAPI, ejemplos y guías.
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.a2a.server import create_a2a_server
from src.a2a.docs import generate_complete_documentation


def main():
    """Generar documentación completa."""
    print("📚 Generando documentación A2A...")
    
    # Crear servidor para extraer rutas
    server = create_a2a_server()
    app = server.create_app()
    
    # Generar documentación
    doc_generator = generate_complete_documentation(app)
    
    print("✅ Documentación generada exitosamente!")
    print("\n📋 Archivos generados:")
    print("   - docs/openapi.json")
    print("   - docs/openapi.yaml") 
    print("   - docs/usage_examples.json")
    print("   - docs/integration_guide.json")
    print("   - docs/README.md")
    
    print("\n🌐 Para visualizar con Swagger UI:")
    print("   1. Instalar: npm install -g swagger-ui-serve")
    print("   2. Ejecutar: swagger-ui-serve docs/openapi.json")
    print("   3. Abrir: http://localhost:3000")


if __name__ == "__main__":
    main() 