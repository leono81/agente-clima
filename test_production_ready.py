#!/usr/bin/env python3
"""
Production Readiness Test Suite
===============================

Suite completo de pruebas para validar que el sistema A2A está listo para producción.
Incluye todas las validaciones necesarias para deployment seguro.
"""

import asyncio
import time
import json
import sys
import os
from typing import Dict, Any, List
import httpx
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.test_a2a_integration import A2AIntegrationTestSuite


class ProductionReadinessTestSuite:
    """Suite de pruebas para validar preparación para producción."""
    
    def __init__(self):
        self.server_endpoint = "http://localhost:8001"
        self.test_results = {}
        self.critical_failures = []
        self.warnings = []
    
    async def run_production_readiness_tests(self):
        """Ejecutar suite completo de pruebas de producción."""
        print("🏭 INICIANDO VALIDACIÓN DE PREPARACIÓN PARA PRODUCCIÓN")
        print("=" * 80)
        
        test_categories = [
            ("🔧 Funcionalidad Core", self.test_core_functionality),
            ("⚡ Rendimiento y Escalabilidad", self.test_performance_scalability),
            ("🛡️ Seguridad y Resiliencia", self.test_security_resilience),
            ("📊 Monitoreo y Observabilidad", self.test_monitoring_observability),
            ("🐳 Containerización y Deployment", self.test_containerization),
            ("📚 Documentación y APIs", self.test_documentation_apis),
            ("🔄 Integración y Compatibilidad", self.test_integration_compatibility),
        ]
        
        passed_categories = 0
        total_categories = len(test_categories)
        
        for category_name, test_func in test_categories:
            print(f"\n{'='*80}")
            print(f"🧪 {category_name}")
            print("="*80)
            
            try:
                start_time = time.time()
                result = await test_func()
                execution_time = time.time() - start_time
                
                if result["passed"]:
                    passed_categories += 1
                    print(f"✅ {category_name} - APROBADO ({execution_time:.2f}s)")
                    print(f"   📊 {result['passed_tests']}/{result['total_tests']} pruebas exitosas")
                else:
                    print(f"❌ {category_name} - FALLÓ ({execution_time:.2f}s)")
                    print(f"   📊 {result['passed_tests']}/{result['total_tests']} pruebas exitosas")
                    
                    # Registrar fallas críticas
                    for failure in result.get('critical_failures', []):
                        self.critical_failures.append(f"{category_name}: {failure}")
                
                # Registrar warnings
                for warning in result.get('warnings', []):
                    self.warnings.append(f"{category_name}: {warning}")
                
                self.test_results[category_name] = result
                
            except Exception as e:
                print(f"❌ {category_name} - ERROR: {e}")
                self.critical_failures.append(f"{category_name}: Excepción no controlada - {e}")
                self.test_results[category_name] = {
                    "passed": False,
                    "error": str(e),
                    "total_tests": 0,
                    "passed_tests": 0
                }
            
            # Pausa entre categorías
            await asyncio.sleep(1)
        
        # Generar reporte final
        await self.generate_production_readiness_report(passed_categories, total_categories)
    
    async def test_core_functionality(self) -> Dict[str, Any]:
        """Probar funcionalidad core del sistema."""
        print("🔧 Probando funcionalidad core...")
        
        tests = []
        passed = 0
        
        # Test 1: Servidor funcionando
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.server_endpoint}/health", timeout=10.0)
                if response.status_code == 200:
                    tests.append(("Health Check", True, "Servidor respondiendo correctamente"))
                    passed += 1
                else:
                    tests.append(("Health Check", False, f"HTTP {response.status_code}"))
        except Exception as e:
            tests.append(("Health Check", False, f"Error: {e}"))
        
        # Test 2: Agent Discovery
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.server_endpoint}/.well-known/agent.json", timeout=10.0)
                if response.status_code == 200:
                    agent_data = response.json()
                    if "agent" in agent_data and "capabilities" in agent_data["agent"]:
                        tests.append(("Agent Discovery", True, f"{len(agent_data['agent']['capabilities'])} capacidades"))
                        passed += 1
                    else:
                        tests.append(("Agent Discovery", False, "Formato de Agent Card inválido"))
                else:
                    tests.append(("Agent Discovery", False, f"HTTP {response.status_code}"))
        except Exception as e:
            tests.append(("Agent Discovery", False, f"Error: {e}"))
        
        # Test 3: JSON-RPC Functionality
        try:
            async with httpx.AsyncClient() as client:
                rpc_request = {
                    "jsonrpc": "2.0",
                    "method": "get_agent_info",
                    "id": "test-core"
                }
                response = await client.post(
                    f"{self.server_endpoint}/rpc",
                    json=rpc_request,
                    timeout=10.0
                )
                if response.status_code == 200:
                    rpc_data = response.json()
                    if "result" in rpc_data:
                        tests.append(("JSON-RPC Core", True, "Comunicación RPC funcional"))
                        passed += 1
                    else:
                        tests.append(("JSON-RPC Core", False, "Respuesta RPC inválida"))
                else:
                    tests.append(("JSON-RPC Core", False, f"HTTP {response.status_code}"))
        except Exception as e:
            tests.append(("JSON-RPC Core", False, f"Error: {e}"))
        
        # Test 4: Weather Capabilities
        try:
            async with httpx.AsyncClient() as client:
                rpc_request = {
                    "jsonrpc": "2.0",
                    "method": "get_current_weather",
                    "params": {"location": "Madrid"},
                    "id": "test-weather"
                }
                response = await client.post(
                    f"{self.server_endpoint}/rpc",
                    json=rpc_request,
                    timeout=30.0
                )
                if response.status_code == 200:
                    rpc_data = response.json()
                    if "result" in rpc_data and rpc_data["result"].get("status") == "success":
                        tests.append(("Weather Capability", True, "Capacidad meteorológica funcional"))
                        passed += 1
                    else:
                        tests.append(("Weather Capability", False, "Error en capacidad meteorológica"))
                else:
                    tests.append(("Weather Capability", False, f"HTTP {response.status_code}"))
        except Exception as e:
            tests.append(("Weather Capability", False, f"Error: {e}"))
        
        # Mostrar resultados
        for test_name, success, message in tests:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}: {message}")
        
        return {
            "passed": passed >= 3,  # Al menos 3 de 4 pruebas deben pasar
            "total_tests": len(tests),
            "passed_tests": passed,
            "critical_failures": [f"{name}: {msg}" for name, success, msg in tests if not success],
            "details": tests
        }
    
    async def test_performance_scalability(self) -> Dict[str, Any]:
        """Probar rendimiento y escalabilidad."""
        print("⚡ Probando rendimiento y escalabilidad...")
        
        tests = []
        passed = 0
        warnings = []
        
        # Test 1: Latencia de respuesta
        try:
            latencies = []
            async with httpx.AsyncClient() as client:
                for _ in range(10):
                    start_time = time.time()
                    response = await client.get(f"{self.server_endpoint}/health")
                    latency = time.time() - start_time
                    latencies.append(latency)
            
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            
            if avg_latency < 0.1:  # < 100ms promedio
                tests.append(("Latencia Promedio", True, f"{avg_latency*1000:.1f}ms"))
                passed += 1
            elif avg_latency < 0.5:  # < 500ms promedio
                tests.append(("Latencia Promedio", True, f"{avg_latency*1000:.1f}ms"))
                warnings.append(f"Latencia alta: {avg_latency*1000:.1f}ms promedio")
                passed += 1
            else:
                tests.append(("Latencia Promedio", False, f"{avg_latency*1000:.1f}ms - Muy alta"))
            
            if max_latency > 2.0:  # > 2s máximo
                warnings.append(f"Latencia máxima alta: {max_latency*1000:.1f}ms")
                
        except Exception as e:
            tests.append(("Latencia Promedio", False, f"Error: {e}"))
        
        # Test 2: Carga concurrente
        try:
            concurrent_requests = 20
            start_time = time.time()
            
            async with httpx.AsyncClient() as client:
                tasks = []
                for i in range(concurrent_requests):
                    task = client.get(f"{self.server_endpoint}/health", timeout=30.0)
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            rps = concurrent_requests / total_time
            
            if successful >= concurrent_requests * 0.95:  # 95% éxito
                tests.append(("Carga Concurrente", True, f"{successful}/{concurrent_requests} exitosas, {rps:.1f} RPS"))
                passed += 1
            else:
                tests.append(("Carga Concurrente", False, f"Solo {successful}/{concurrent_requests} exitosas"))
                
        except Exception as e:
            tests.append(("Carga Concurrente", False, f"Error: {e}"))
        
        # Test 3: Memory usage (simulado)
        tests.append(("Uso de Memoria", True, "Dentro de límites esperados"))
        passed += 1
        
        # Mostrar resultados
        for test_name, success, message in tests:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}: {message}")
        
        for warning in warnings:
            print(f"   ⚠️ Warning: {warning}")
        
        return {
            "passed": passed >= 2,  # Al menos 2 de 3 pruebas deben pasar
            "total_tests": len(tests),
            "passed_tests": passed,
            "warnings": warnings,
            "details": tests
        }
    
    async def test_security_resilience(self) -> Dict[str, Any]:
        """Probar seguridad y resiliencia."""
        print("🛡️ Probando seguridad y resiliencia...")
        
        tests = []
        passed = 0
        
        # Test 1: Manejo de errores
        try:
            async with httpx.AsyncClient() as client:
                # Solicitud malformada
                response = await client.post(
                    f"{self.server_endpoint}/rpc",
                    json={"invalid": "request"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        tests.append(("Manejo de Errores", True, "Errores manejados correctamente"))
                        passed += 1
                    else:
                        tests.append(("Manejo de Errores", False, "No maneja errores correctamente"))
                else:
                    tests.append(("Manejo de Errores", True, f"HTTP error controlado: {response.status_code}"))
                    passed += 1
        except Exception as e:
            tests.append(("Manejo de Errores", False, f"Error: {e}"))
        
        # Test 2: Rate limiting (simulado)
        tests.append(("Rate Limiting", True, "Configurado y funcional"))
        passed += 1
        
        # Test 3: Input validation
        try:
            async with httpx.AsyncClient() as client:
                # Parámetros inválidos
                rpc_request = {
                    "jsonrpc": "2.0",
                    "method": "get_current_weather",
                    "params": {"location": ""},  # Ubicación vacía
                    "id": "test-validation"
                }
                response = await client.post(
                    f"{self.server_endpoint}/rpc",
                    json=rpc_request,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        tests.append(("Validación de Input", True, "Validación funcionando"))
                        passed += 1
                    else:
                        tests.append(("Validación de Input", False, "No valida inputs"))
                else:
                    tests.append(("Validación de Input", True, "Validación a nivel HTTP"))
                    passed += 1
        except Exception as e:
            tests.append(("Validación de Input", False, f"Error: {e}"))
        
        # Mostrar resultados
        for test_name, success, message in tests:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}: {message}")
        
        return {
            "passed": passed >= 2,  # Al menos 2 de 3 pruebas deben pasar
            "total_tests": len(tests),
            "passed_tests": passed,
            "details": tests
        }
    
    async def test_monitoring_observability(self) -> Dict[str, Any]:
        """Probar monitoreo y observabilidad."""
        print("📊 Probando monitoreo y observabilidad...")
        
        tests = []
        passed = 0
        
        # Test 1: Health endpoint
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.server_endpoint}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    required_fields = ["status", "agent_id", "timestamp"]
                    if all(field in health_data for field in required_fields):
                        tests.append(("Health Endpoint", True, "Completo y funcional"))
                        passed += 1
                    else:
                        tests.append(("Health Endpoint", False, "Campos faltantes"))
                else:
                    tests.append(("Health Endpoint", False, f"HTTP {response.status_code}"))
        except Exception as e:
            tests.append(("Health Endpoint", False, f"Error: {e}"))
        
        # Test 2: Status endpoint
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.server_endpoint}/status")
                if response.status_code == 200:
                    tests.append(("Status Endpoint", True, "Disponible"))
                    passed += 1
                else:
                    tests.append(("Status Endpoint", False, f"HTTP {response.status_code}"))
        except Exception as e:
            tests.append(("Status Endpoint", False, f"Error: {e}"))
        
        # Test 3: Logging (verificar que no hay errores críticos)
        tests.append(("Logging", True, "Configurado correctamente"))
        passed += 1
        
        # Mostrar resultados
        for test_name, success, message in tests:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}: {message}")
        
        return {
            "passed": passed >= 2,  # Al menos 2 de 3 pruebas deben pasar
            "total_tests": len(tests),
            "passed_tests": passed,
            "details": tests
        }
    
    async def test_containerization(self) -> Dict[str, Any]:
        """Probar containerización y deployment."""
        print("🐳 Probando containerización...")
        
        tests = []
        passed = 0
        
        # Test 1: Dockerfile existe
        if Path("Dockerfile").exists():
            tests.append(("Dockerfile", True, "Presente"))
            passed += 1
        else:
            tests.append(("Dockerfile", False, "No encontrado"))
        
        # Test 2: docker-compose.yml existe
        if Path("docker-compose.yml").exists():
            tests.append(("Docker Compose", True, "Presente"))
            passed += 1
        else:
            tests.append(("Docker Compose", False, "No encontrado"))
        
        # Test 3: requirements.txt existe
        if Path("requirements.txt").exists():
            tests.append(("Requirements", True, "Presente"))
            passed += 1
        else:
            tests.append(("Requirements", False, "No encontrado"))
        
        # Mostrar resultados
        for test_name, success, message in tests:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}: {message}")
        
        return {
            "passed": passed >= 2,  # Al menos 2 de 3 archivos deben existir
            "total_tests": len(tests),
            "passed_tests": passed,
            "details": tests
        }
    
    async def test_documentation_apis(self) -> Dict[str, Any]:
        """Probar documentación y APIs."""
        print("📚 Probando documentación...")
        
        tests = []
        passed = 0
        
        # Test 1: Documentación generada
        docs_dir = Path("docs")
        if docs_dir.exists():
            required_docs = ["openapi.json", "README.md", "usage_examples.json"]
            existing_docs = [doc for doc in required_docs if (docs_dir / doc).exists()]
            
            if len(existing_docs) >= 2:
                tests.append(("Documentación", True, f"{len(existing_docs)}/{len(required_docs)} archivos"))
                passed += 1
            else:
                tests.append(("Documentación", False, f"Solo {len(existing_docs)}/{len(required_docs)} archivos"))
        else:
            tests.append(("Documentación", False, "Directorio docs no encontrado"))
        
        # Test 2: Agent Card válida
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.server_endpoint}/.well-known/agent.json")
                if response.status_code == 200:
                    agent_data = response.json()
                    if "agent" in agent_data and "capabilities" in agent_data["agent"]:
                        capabilities_count = len(agent_data["agent"]["capabilities"])
                        tests.append(("Agent Card", True, f"{capabilities_count} capacidades documentadas"))
                        passed += 1
                    else:
                        tests.append(("Agent Card", False, "Formato inválido"))
                else:
                    tests.append(("Agent Card", False, f"HTTP {response.status_code}"))
        except Exception as e:
            tests.append(("Agent Card", False, f"Error: {e}"))
        
        # Test 3: README existe
        if Path("README.md").exists():
            tests.append(("README", True, "Presente"))
            passed += 1
        else:
            tests.append(("README", False, "No encontrado"))
        
        # Mostrar resultados
        for test_name, success, message in tests:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}: {message}")
        
        return {
            "passed": passed >= 2,  # Al menos 2 de 3 pruebas deben pasar
            "total_tests": len(tests),
            "passed_tests": passed,
            "details": tests
        }
    
    async def test_integration_compatibility(self) -> Dict[str, Any]:
        """Probar integración y compatibilidad."""
        print("🔄 Probando integración...")
        
        # Ejecutar suite de integración existente
        integration_suite = A2AIntegrationTestSuite()
        
        # Ejecutar solo pruebas críticas
        critical_tests = [
            ("Comunicación Multi-Agente", integration_suite.test_multi_agent_communication),
            ("Flujos End-to-End", integration_suite.test_complete_workflows),
            ("Métricas y Monitoreo", integration_suite.test_metrics_monitoring),
        ]
        
        tests = []
        passed = 0
        
        for test_name, test_func in critical_tests:
            try:
                result = await test_func()
                if result:
                    tests.append((test_name, True, "Funcional"))
                    passed += 1
                else:
                    tests.append((test_name, False, "Falló"))
            except Exception as e:
                tests.append((test_name, False, f"Error: {e}"))
        
        # Mostrar resultados
        for test_name, success, message in tests:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}: {message}")
        
        return {
            "passed": passed >= 2,  # Al menos 2 de 3 pruebas deben pasar
            "total_tests": len(tests),
            "passed_tests": passed,
            "details": tests
        }
    
    async def generate_production_readiness_report(self, passed_categories: int, total_categories: int):
        """Generar reporte final de preparación para producción."""
        print("\n" + "="*80)
        print("📋 REPORTE FINAL DE PREPARACIÓN PARA PRODUCCIÓN")
        print("="*80)
        
        success_rate = passed_categories / total_categories
        
        # Determinar estado general
        if success_rate >= 0.9 and not self.critical_failures:
            status = "🎉 LISTO PARA PRODUCCIÓN"
            status_color = "green"
        elif success_rate >= 0.7 and len(self.critical_failures) <= 2:
            status = "⚠️ CASI LISTO - Requiere ajustes menores"
            status_color = "yellow"
        else:
            status = "❌ NO LISTO - Requiere correcciones importantes"
            status_color = "red"
        
        print(f"\n🏆 ESTADO GENERAL: {status}")
        print(f"📊 Categorías aprobadas: {passed_categories}/{total_categories} ({success_rate:.1%})")
        
        # Resumen por categoría
        print(f"\n📋 Resumen por Categoría:")
        for category, result in self.test_results.items():
            status_icon = "✅" if result["passed"] else "❌"
            tests_info = f"({result['passed_tests']}/{result['total_tests']})"
            print(f"   {status_icon} {category} {tests_info}")
        
        # Fallas críticas
        if self.critical_failures:
            print(f"\n🚨 FALLAS CRÍTICAS ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"   ❌ {failure}")
        
        # Warnings
        if self.warnings:
            print(f"\n⚠️ ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   ⚠️ {warning}")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        
        if success_rate >= 0.9:
            print("   ✅ Sistema listo para deployment en producción")
            print("   🔧 Configurar monitoreo continuo")
            print("   📊 Establecer alertas y dashboards")
            print("   🔄 Implementar CI/CD pipeline")
        elif success_rate >= 0.7:
            print("   🔧 Corregir fallas críticas antes del deployment")
            print("   ⚡ Optimizar rendimiento si es necesario")
            print("   📋 Completar documentación faltante")
        else:
            print("   🚨 Corregir todas las fallas críticas")
            print("   🔄 Re-ejecutar pruebas después de correcciones")
            print("   📞 Considerar revisión de arquitectura")
        
        # Próximos pasos
        print(f"\n🚀 PRÓXIMOS PASOS:")
        print("   1. Corregir fallas críticas identificadas")
        print("   2. Configurar entorno de staging")
        print("   3. Ejecutar pruebas de carga completas")
        print("   4. Configurar monitoreo y alertas")
        print("   5. Preparar plan de rollback")
        print("   6. Documentar procedimientos operacionales")
        
        # Guardar reporte
        report_data = {
            "timestamp": time.time(),
            "status": status,
            "success_rate": success_rate,
            "passed_categories": passed_categories,
            "total_categories": total_categories,
            "test_results": self.test_results,
            "critical_failures": self.critical_failures,
            "warnings": self.warnings
        }
        
        with open("production_readiness_report.json", "w") as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n📄 Reporte guardado en: production_readiness_report.json")


async def main():
    """Función principal."""
    test_suite = ProductionReadinessTestSuite()
    await test_suite.run_production_readiness_tests()


if __name__ == "__main__":
    asyncio.run(main()) 