#!/usr/bin/env python3
"""
A2A Integration Tests - Suite Completo End-to-End
================================================

Suite de pruebas de integración completo para validar:
- Comunicación A2A multi-agente
- Performance bajo carga
- Resiliencia ante fallos
- Flujos completos de principio a fin
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import httpx

from src.a2a.client import create_a2a_client
from src.a2a.server import create_a2a_server


class A2AIntegrationTestSuite:
    """Suite completo de pruebas de integración A2A."""
    
    def __init__(self):
        self.server_endpoint = "http://localhost:8001"
        self.test_results = {}
        self.performance_metrics = {}
    
    async def run_complete_test_suite(self):
        """Ejecutar suite completo de pruebas."""
        print("🧪 Iniciando Suite Completo de Testing A2A")
        print("=" * 60)
        
        test_suites = [
            ("🔗 Comunicación Multi-Agente", self.test_multi_agent_communication),
            ("⚡ Performance y Carga", self.test_performance_load),
            ("🛡️ Resiliencia y Recuperación", self.test_resilience_recovery),
            ("🌍 Flujos End-to-End Completos", self.test_complete_workflows),
            ("🔄 Gestión de Tareas Asíncronas", self.test_async_task_management),
            ("📊 Métricas y Monitoreo", self.test_metrics_monitoring),
        ]
        
        passed = 0
        total = len(test_suites)
        
        for suite_name, test_func in test_suites:
            print(f"\n{'='*60}")
            print(f"🧪 {suite_name}")
            print("="*60)
            
            try:
                start_time = time.time()
                result = await test_func()
                execution_time = time.time() - start_time
                
                if result:
                    passed += 1
                    print(f"✅ {suite_name} - EXITOSO ({execution_time:.2f}s)")
                    self.test_results[suite_name] = {"status": "PASS", "time": execution_time}
                else:
                    print(f"❌ {suite_name} - FALLÓ ({execution_time:.2f}s)")
                    self.test_results[suite_name] = {"status": "FAIL", "time": execution_time}
                    
            except Exception as e:
                print(f"❌ {suite_name} - ERROR: {e}")
                self.test_results[suite_name] = {"status": "ERROR", "error": str(e)}
            
            # Pausa entre suites
            await asyncio.sleep(1)
        
        # Reporte final
        await self.generate_final_report(passed, total)
    
    async def test_multi_agent_communication(self) -> bool:
        """Probar comunicación entre múltiples agentes simulados."""
        print("🔗 Probando comunicación multi-agente...")
        
        async with create_a2a_client() as client:
            # Simular múltiples agentes consultando clima
            cities = ["Madrid", "Buenos Aires", "Tokyo", "New York", "London"]
            tasks = []
            
            print(f"📡 Simulando {len(cities)} agentes consultando clima simultáneamente...")
            
            for city in cities:
                task = client.execute_capability_sync(
                    self.server_endpoint,
                    "get_current_weather",
                    {"location": city}
                )
                tasks.append(task)
            
            # Ejecutar todas las consultas en paralelo
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"❌ Error en {cities[i]}: {result}")
                elif result and result.get("status") == "success":
                    temp = result.get("current_weather", {}).get("temperature", "N/A")
                    print(f"✅ {cities[i]}: {temp}°C")
                    successful += 1
                else:
                    print(f"⚠️ {cities[i]}: Respuesta inválida")
            
            success_rate = successful / len(cities)
            print(f"📊 Tasa de éxito: {success_rate:.1%} ({successful}/{len(cities)})")
            
            return success_rate >= 0.8  # 80% de éxito mínimo
    
    async def test_performance_load(self) -> bool:
        """Probar rendimiento bajo carga."""
        print("⚡ Probando performance bajo carga...")
        
        async with create_a2a_client() as client:
            # Test de carga: 50 solicitudes concurrentes
            num_requests = 50
            print(f"🚀 Enviando {num_requests} solicitudes concurrentes...")
            
            start_time = time.time()
            
            tasks = []
            for i in range(num_requests):
                city = ["Madrid", "Paris", "London", "Berlin", "Rome"][i % 5]
                task = client.execute_capability_sync(
                    self.server_endpoint,
                    "search_locations",
                    {"query": city, "limit": 1}
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Analizar resultados
            successful = sum(1 for r in results if not isinstance(r, Exception) and r)
            failed = len(results) - successful
            
            requests_per_second = num_requests / total_time
            
            print(f"📊 Resultados de carga:")
            print(f"   ✅ Exitosas: {successful}")
            print(f"   ❌ Fallidas: {failed}")
            print(f"   ⏱️ Tiempo total: {total_time:.2f}s")
            print(f"   🚀 RPS: {requests_per_second:.1f}")
            
            # Guardar métricas
            self.performance_metrics["load_test"] = {
                "requests": num_requests,
                "successful": successful,
                "failed": failed,
                "total_time": total_time,
                "rps": requests_per_second
            }
            
            # Criterios de éxito: >80% éxito y >5 RPS
            return successful / num_requests >= 0.8 and requests_per_second >= 5
    
    async def test_resilience_recovery(self) -> bool:
        """Probar resiliencia y recuperación ante fallos."""
        print("🛡️ Probando resiliencia ante fallos...")
        
        async with create_a2a_client() as client:
            # Test 1: Ubicaciones inválidas
            print("1. Probando manejo de ubicaciones inválidas...")
            invalid_locations = ["", "XYZ123", "NonExistentCity", "12345"]
            
            resilience_score = 0
            for location in invalid_locations:
                try:
                    result = await client.execute_capability_sync(
                        self.server_endpoint,
                        "get_current_weather",
                        {"location": location}
                    )
                    
                    if result and result.get("status") == "error":
                        print(f"✅ Manejo correcto de '{location}': Error controlado")
                        resilience_score += 1
                    else:
                        print(f"⚠️ '{location}': Respuesta inesperada")
                        
                except Exception as e:
                    print(f"✅ Manejo correcto de '{location}': Excepción controlada")
                    resilience_score += 1
            
            # Test 2: Parámetros malformados
            print("2. Probando manejo de parámetros malformados...")
            malformed_requests = [
                {"method": "get_current_weather", "params": {}},  # Sin ubicación
                {"method": "search_locations", "params": {"limit": -1}},  # Límite inválido
                {"method": "nonexistent_method", "params": {"test": True}},  # Método inexistente
            ]
            
            for req in malformed_requests:
                try:
                    # Hacer solicitud RPC directa
                    async with httpx.AsyncClient() as http_client:
                        response = await http_client.post(
                            f"{self.server_endpoint}/rpc",
                            json={
                                "jsonrpc": "2.0",
                                "id": "test",
                                **req
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            if "error" in data:
                                print(f"✅ Error controlado para {req['method']}")
                                resilience_score += 1
                            else:
                                print(f"⚠️ {req['method']}: Debería haber retornado error")
                        else:
                            print(f"✅ HTTP error controlado para {req['method']}")
                            resilience_score += 1
                            
                except Exception as e:
                    print(f"✅ Excepción controlada para {req['method']}")
                    resilience_score += 1
            
            total_tests = len(invalid_locations) + len(malformed_requests)
            resilience_rate = resilience_score / total_tests
            
            print(f"📊 Puntuación de resiliencia: {resilience_rate:.1%} ({resilience_score}/{total_tests})")
            
            return resilience_rate >= 0.8
    
    async def test_complete_workflows(self) -> bool:
        """Probar flujos completos end-to-end."""
        print("🌍 Probando flujos end-to-end completos...")
        
        workflows = [
            {
                "name": "Flujo de Consulta Meteorológica Completa",
                "steps": [
                    ("search_locations", {"query": "Barcelona", "limit": 3}),
                    ("get_current_weather", {"location": "Barcelona"}),
                ]
            },
            {
                "name": "Flujo de Comparación Multi-Ciudad",
                "steps": [
                    ("get_current_weather", {"location": "Madrid"}),
                    ("get_current_weather", {"location": "Barcelona"}),
                    ("get_current_weather", {"location": "Valencia"}),
                ]
            }
        ]
        
        async with create_a2a_client() as client:
            workflow_results = []
            
            for workflow in workflows:
                print(f"\n🔄 Ejecutando: {workflow['name']}")
                workflow_success = True
                step_results = []
                
                for i, (method, params) in enumerate(workflow['steps'], 1):
                    print(f"   Paso {i}: {method}")
                    
                    try:
                        result = await client.execute_capability_sync(
                            self.server_endpoint,
                            method,
                            params
                        )
                        
                        if result and result.get("status") == "success":
                            print(f"   ✅ Paso {i} exitoso")
                            step_results.append(result)
                        else:
                            print(f"   ❌ Paso {i} falló")
                            workflow_success = False
                            break
                            
                    except Exception as e:
                        print(f"   ❌ Paso {i} error: {e}")
                        workflow_success = False
                        break
                
                workflow_results.append(workflow_success)
                
                if workflow_success:
                    print(f"✅ {workflow['name']} - COMPLETADO")
                else:
                    print(f"❌ {workflow['name']} - FALLÓ")
            
            success_rate = sum(workflow_results) / len(workflow_results)
            print(f"\n📊 Tasa de éxito de workflows: {success_rate:.1%}")
            
            return success_rate >= 0.8
    
    async def test_async_task_management(self) -> bool:
        """Probar gestión de tareas asíncronas."""
        print("🔄 Probando gestión de tareas asíncronas...")
        
        async with create_a2a_client() as client:
            # Enviar múltiples tareas asíncronas
            tasks_to_submit = [
                ("search_locations", {"query": "Tokyo", "limit": 2}),
                ("search_locations", {"query": "Seoul", "limit": 2}),
                ("search_locations", {"query": "Beijing", "limit": 2}),
            ]
            
            submitted_tasks = []
            
            print(f"📤 Enviando {len(tasks_to_submit)} tareas asíncronas...")
            
            for capability, params in tasks_to_submit:
                task_id = await client.submit_task(
                    self.server_endpoint,
                    capability,
                    params
                )
                
                if task_id:
                    submitted_tasks.append(task_id)
                    print(f"✅ Tarea enviada: {task_id[:8]}...")
                else:
                    print("❌ Error enviando tarea")
            
            # Monitorear progreso de tareas
            print("📊 Monitoreando progreso...")
            completed_tasks = 0
            max_wait_time = 30  # 30 segundos máximo
            start_time = time.time()
            
            while completed_tasks < len(submitted_tasks) and (time.time() - start_time) < max_wait_time:
                for task_id in submitted_tasks:
                    status = await client.get_task_status(self.server_endpoint, task_id)
                    
                    if status and status.get("status") == "completed":
                        if task_id not in [t for t in submitted_tasks if t == task_id]:  # Evitar contar duplicados
                            completed_tasks += 1
                            print(f"✅ Tarea completada: {task_id[:8]}...")
                
                await asyncio.sleep(1)
            
            completion_rate = completed_tasks / len(submitted_tasks)
            execution_time = time.time() - start_time
            
            print(f"📊 Resultados de tareas asíncronas:")
            print(f"   ✅ Completadas: {completed_tasks}/{len(submitted_tasks)}")
            print(f"   ⏱️ Tiempo: {execution_time:.1f}s")
            print(f"   📈 Tasa de completado: {completion_rate:.1%}")
            
            return completion_rate >= 0.8
    
    async def test_metrics_monitoring(self) -> bool:
        """Probar métricas y monitoreo."""
        print("📊 Probando métricas y monitoreo...")
        
        # Test de endpoints de monitoreo
        async with httpx.AsyncClient() as client:
            endpoints_to_test = [
                ("/health", "Health Check"),
                ("/status", "Status Check"),
                ("/.well-known/agent.json", "Agent Discovery"),
                ("/tasks", "Task Management"),
            ]
            
            monitoring_score = 0
            
            for endpoint, description in endpoints_to_test:
                try:
                    response = await client.get(f"{self.server_endpoint}{endpoint}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ {description}: OK")
                        monitoring_score += 1
                        
                        # Validar estructura de respuesta
                        if endpoint == "/health" and "status" in data:
                            print(f"   Status: {data['status']}")
                        elif endpoint == "/status" and "agent_id" in data:
                            print(f"   Agent ID: {data['agent_id']}")
                        elif endpoint == "/.well-known/agent.json" and "agent" in data:
                            print(f"   Agent Name: {data['agent']['name']}")
                            
                    else:
                        print(f"❌ {description}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ {description}: Error - {e}")
            
            monitoring_rate = monitoring_score / len(endpoints_to_test)
            print(f"📊 Puntuación de monitoreo: {monitoring_rate:.1%}")
            
            return monitoring_rate >= 0.8
    
    async def generate_final_report(self, passed: int, total: int):
        """Generar reporte final de testing."""
        print("\n" + "="*60)
        print("📋 REPORTE FINAL DE TESTING A2A")
        print("="*60)
        
        success_rate = passed / total
        
        print(f"📊 Resumen General:")
        print(f"   ✅ Suites exitosos: {passed}/{total}")
        print(f"   📈 Tasa de éxito: {success_rate:.1%}")
        
        if success_rate >= 0.8:
            print("🎉 ¡SISTEMA A2A LISTO PARA PRODUCCIÓN!")
        elif success_rate >= 0.6:
            print("⚠️ Sistema funcional, requiere optimizaciones")
        else:
            print("❌ Sistema requiere correcciones importantes")
        
        # Detalles por suite
        print(f"\n📋 Detalles por Suite:")
        for suite_name, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            time_info = f"({result.get('time', 0):.2f}s)" if "time" in result else ""
            print(f"   {status_icon} {suite_name} {time_info}")
            
            if result["status"] == "ERROR":
                print(f"      Error: {result.get('error', 'N/A')}")
        
        # Métricas de performance
        if self.performance_metrics:
            print(f"\n⚡ Métricas de Performance:")
            for metric_name, metrics in self.performance_metrics.items():
                if metric_name == "load_test":
                    print(f"   🚀 Test de Carga:")
                    print(f"      Solicitudes: {metrics['requests']}")
                    print(f"      RPS: {metrics['rps']:.1f}")
                    print(f"      Éxito: {metrics['successful']}/{metrics['requests']}")


async def main():
    """Función principal para ejecutar el suite de testing."""
    test_suite = A2AIntegrationTestSuite()
    await test_suite.run_complete_test_suite()


if __name__ == "__main__":
    asyncio.run(main()) 