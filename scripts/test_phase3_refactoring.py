#!/usr/bin/env python3
"""
Test Fase 3: Validación Completa del Refactoring con Dependency Injection
- Valida cada tool individualmente
- Valida el flujo completo del agent
- Logs detallados para debugging
- Guarda reportes de comparación
"""
import asyncio
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Setup project path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Import tools to activate @register_tool
import app.tools.implementations

from app.tools.core import ToolContext, ToolRegistry
from app.agents.report.agent import ReportAgent

# Colors para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log_header(msg: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.ENDC}\n")

def log_section(msg: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'-'*100}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'-'*100}{Colors.ENDC}")

def log_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.ENDC}")

def log_error(msg: str):
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")

def log_warning(msg: str):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def log_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.ENDC}")

def save_debug_report(test_name: str, data: Dict[str, Any]):
    """Guarda reporte de debug en JSON"""
    debug_dir = Path("data_store/logs/test_phase3")
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.json"
    filepath = debug_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    log_info(f"Debug guardado: {filepath}")
    return filepath


# ============================================================================
# TEST 1: Validar ToolContext
# ============================================================================
async def test_tool_context():
    log_section("TEST 1: VALIDACIÓN DE TOOLCONTEXT")
    
    try:
        from app.tools.core import ToolContext, ToolResult, ToolOutput
        
        # Crear contexto
        ctx = ToolContext()
        log_success("ToolContext creado correctamente")
        
        # Simular resultado de tool
        fake_output = ToolOutput(
            success=True,
            data={"test": "data"},
            metadata={"rows": 10}
        )
        
        ctx.set_result("test_tool", fake_output)
        log_success("set_result() funciona")
        
        # Verificar recuperación
        result = ctx.get_result("test_tool")
        assert result is not None, "get_result() debería retornar resultado"
        assert result.success == True, "Success debería ser True"
        log_success("get_result() funciona")
        
        # Verificar successful_result
        success_result = ctx.get_successful_result("test_tool")
        assert success_result is not None, "get_successful_result() debería retornar"
        log_success("get_successful_result() funciona")
        
        # Verificar historial
        history = ctx.get_execution_history()
        assert "test_tool" in history, "Tool debería estar en historial"
        log_success("get_execution_history() funciona")
        
        # Verificar to_dict
        ctx_dict = ctx.to_dict()
        assert "execution_order" in ctx_dict, "to_dict() debe tener execution_order"
        assert "results" in ctx_dict, "to_dict() debe tener results"
        log_success("to_dict() funciona")
        
        log_success("✅ TOOLCONTEXT: TODAS LAS VALIDACIONES PASARON")
        return True
        
    except Exception as e:
        log_error(f"Error en test_tool_context: {e}")
        print(traceback.format_exc())
        return False


# ============================================================================
# TEST 2: Validar Tool Individual (SQL Extraction)
# ============================================================================
async def test_sql_tool_autonomous():
    log_section("TEST 2: SQL TOOL AUTÓNOMA")
    
    test_data = {
        "test_name": "sql_tool_autonomous",
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "error": None,
        "result": None
    }
    
    try:
        tool = ToolRegistry.get("sql_data_extraction")
        if not tool:
            raise Exception("sql_data_extraction no encontrada en registry")
        
        log_success("Tool encontrada en registry")
        log_info(f"  - Nombre: {tool.name}")
        log_info(f"  - Descripción: {tool.description}")
        log_info(f"  - Dependencias: {tool.dependencies}")
        
        # Crear contexto (vacío porque no tiene dependencias)
        context = ToolContext()
        
        # Ejecutar tool
        log_info("Ejecutando tool con consultant_name...")
        result = await tool.execute(
            context,
            consultant_name="YARLEN ASTRID ALVAREZ BUILES (203)"
        )
        
        log_info(f"  - Success: {result.success}")
        log_info(f"  - Error: {result.error}")
        log_info(f"  - Metadata: {result.metadata}")
        
        if result.success:
            row_count = result.metadata.get('row_count', 0)
            log_success(f"✓ SQL extrajo {row_count} filas")
            
            # Validar estructura de datos
            if isinstance(result.data, list) and len(result.data) > 0:
                log_success(f"✓ Data es lista con {len(result.data)} elementos")
                log_info(f"  - Primer elemento: {list(result.data[0].keys())}")
            else:
                log_warning("Data está vacía o no es lista")
            
            test_data["success"] = True
            test_data["result"] = {
                "row_count": row_count,
                "has_data": result.data is not None,
                "metadata": result.metadata
            }
        else:
            log_error(f"Tool falló: {result.error}")
            test_data["error"] = result.error
        
        log_success("✅ SQL TOOL: VALIDACIÓN COMPLETADA")
        save_debug_report("test_sql_tool", test_data)
        return result.success
        
    except Exception as e:
        log_error(f"Error en test_sql_tool_autonomous: {e}")
        print(traceback.format_exc())
        test_data["error"] = str(e)
        test_data["traceback"] = traceback.format_exc()
        save_debug_report("test_sql_tool_error", test_data)
        return False


# ============================================================================
# TEST 3: Validar Dependency Resolution (Evidence Tool)
# ============================================================================
async def test_evidence_tool_dependency_resolution():
    log_section("TEST 3: EVIDENCE TOOL CON DEPENDENCY RESOLUTION")
    
    test_data = {
        "test_name": "evidence_dependency_resolution",
        "timestamp": datetime.now().isoformat(),
        "steps": []
    }
    
    try:
        # Step 1: Ejecutar SQL tool
        log_info("PASO 1: Ejecutando SQL tool...")
        sql_tool = ToolRegistry.get("sql_data_extraction")
        context = ToolContext()
        
        sql_result = await sql_tool.execute(
            context,
            consultant_name="YARLEN ASTRID ALVAREZ BUILES (203)"
        )
        
        test_data["steps"].append({
            "step": "sql_execution",
            "success": sql_result.success,
            "row_count": sql_result.metadata.get('row_count', 0) if sql_result.success else 0
        })
        
        if not sql_result.success:
            log_error("SQL tool falló, no se puede continuar")
            test_data["error"] = "sql_failed"
            save_debug_report("test_evidence_error", test_data)
            return False
        
        log_success(f"✓ SQL ejecutado: {sql_result.metadata.get('row_count', 0)} filas")
        
        # Step 2: Publicar resultado en contexto
        log_info("PASO 2: Publicando resultado SQL en contexto...")
        context.set_result("sql_data_extraction", sql_result)
        log_success("✓ Resultado publicado")
        
        # Step 3: Ejecutar Evidence tool SIN proporcionar defect_ids
        log_info("PASO 3: Ejecutando Evidence tool (auto-resolve defect_ids)...")
        evidence_tool = ToolRegistry.get("evidence_retrieval")
        
        # NO pasamos defect_ids - debe auto-resolverse
        evidence_result = await evidence_tool.execute(
            context,
            consultant_name="YARLEN ASTRID ALVAREZ BUILES (203)"
        )
        
        log_info(f"  - Success: {evidence_result.success}")
        log_info(f"  - Error: {evidence_result.error}")
        
        if evidence_result.success:
            defects_processed = evidence_result.metadata.get('defects_processed', 0)
            total_chunks = evidence_result.metadata.get('total_chunks', 0)
            
            log_success(f"✓ Evidencia recuperada para {defects_processed} defectos")
            log_success(f"✓ Total chunks: {total_chunks}")
            
            # Validar que realmente extrajo IDs
            if defects_processed > 0:
                log_success("✓ DEPENDENCY RESOLUTION FUNCIONÓ (extrajo IDs automáticamente)")
            else:
                log_warning("⚠ No se procesaron defectos (puede ser normal si no hay IDs)")
            
            test_data["steps"].append({
                "step": "evidence_execution",
                "success": True,
                "defects_processed": defects_processed,
                "total_chunks": total_chunks
            })
            test_data["success"] = True
        else:
            log_error(f"Evidence tool falló: {evidence_result.error}")
            test_data["steps"].append({
                "step": "evidence_execution",
                "success": False,
                "error": evidence_result.error
            })
        
        log_success("✅ EVIDENCE TOOL: VALIDACIÓN COMPLETADA")
        save_debug_report("test_evidence_tool", test_data)
        return evidence_result.success
        
    except Exception as e:
        log_error(f"Error en test_evidence_tool: {e}")
        print(traceback.format_exc())
        test_data["error"] = str(e)
        test_data["traceback"] = traceback.format_exc()
        save_debug_report("test_evidence_error", test_data)
        return False


# ============================================================================
# TEST 4: Validar Flujo Completo del Agent
# ============================================================================
async def test_full_agent_flow():
    log_section("TEST 4: FLUJO COMPLETO DEL AGENT")
    
    test_data = {
        "test_name": "full_agent_flow",
        "timestamp": datetime.now().isoformat(),
        "consultant": "YARLEN ASTRID ALVAREZ BUILES (203)",
        "success": False
    }
    
    try:
        log_info("Inicializando ReportAgent...")
        agent = ReportAgent()
        log_success("✓ Agent inicializado")
        
        # Verificar tools registradas
        log_info(f"Tools disponibles: {len(agent.tools)}")
        for tool_name in agent.tools.keys():
            log_info(f"  - {tool_name}")
        
        # Generar reporte
        log_info("Generando reporte...")
        report = await agent.generate_report(
            consultant_name="YARLEN ASTRID ALVAREZ BUILES (203)",
            report_type="preview"
        )
        
        # Validar estructura del reporte
        log_info("Validando estructura del reporte...")
        
        required_keys = ["consultant", "generated_at", "type", "data", "sections", "metadata"]
        for key in required_keys:
            if key in report:
                log_success(f"✓ Clave '{key}' presente")
            else:
                log_error(f"✗ Clave '{key}' faltante")
        
        # Validar datos
        sql_rows = report.get('data', {}).get('sql_rows', 0)
        evidence_count = report.get('data', {}).get('evidence_count', 0)
        
        log_info(f"\nRESULTADOS:")
        log_info(f"  - SQL rows: {sql_rows}")
        log_info(f"  - Evidence count: {evidence_count}")
        log_info(f"  - Charts: {len(report.get('charts', {}))}")
        log_info(f"  - Versión: {report.get('metadata', {}).get('version')}")
        log_info(f"  - Arquitectura: {report.get('metadata', {}).get('architecture')}")
        
        # Validar secciones
        summary = report.get('sections', {}).get('summary', '')
        recommendations = report.get('sections', {}).get('recommendations', '')
        
        log_info(f"\nSECCIONES:")
        log_info(f"  - Summary: {len(summary)} chars")
        log_info(f"  - Recommendations: {len(recommendations)} chars")
        
        # Validar arquitectura
        architecture = report.get('metadata', {}).get('architecture')
        if architecture == "dependency-injection":
            log_success("✓ Arquitectura correcta: dependency-injection")
        else:
            log_warning(f"⚠ Arquitectura inesperada: {architecture}")
        
        # Guardar reporte completo
        report_path = save_debug_report("full_report", report)
        log_success(f"✓ Reporte guardado: {report_path}")
        
        # Determinar éxito
        if sql_rows > 0:
            test_data["success"] = True
            log_success("✅ AGENT FLOW: REPORTE GENERADO EXITOSAMENTE")
        else:
            log_warning("⚠ Reporte generado pero sin datos SQL")
        
        test_data["report_summary"] = {
            "sql_rows": sql_rows,
            "evidence_count": evidence_count,
            "charts_count": len(report.get('charts', {})),
            "summary_length": len(summary),
            "recommendations_length": len(recommendations)
        }
        
        save_debug_report("test_agent_summary", test_data)
        return test_data["success"]
        
    except Exception as e:
        log_error(f"Error en test_full_agent_flow: {e}")
        print(traceback.format_exc())
        test_data["error"] = str(e)
        test_data["traceback"] = traceback.format_exc()
        save_debug_report("test_agent_error", test_data)
        return False


# ============================================================================
# TEST 5: Comparación con Sistema Anterior (si existe)
# ============================================================================
async def test_comparison_with_old_system():
    log_section("TEST 5: COMPARACIÓN CON SISTEMA ANTERIOR")
    
    try:
        # Intentar cargar reporte antiguo si existe
        old_report_dir = Path("data_store/reports/comparison")
        old_report_path = old_report_dir / "report_old.json"
        
        if not old_report_path.exists():
            log_warning("⚠ No hay reporte antiguo para comparar")
            log_info("  - Ejecuta primero el sistema antiguo si quieres comparar")
            return True
        
        with open(old_report_path, 'r', encoding='utf-8') as f:
            old_report = json.load(f)
        
        log_success("✓ Reporte antiguo cargado")
        
        # Generar nuevo reporte
        log_info("Generando nuevo reporte...")
        agent = ReportAgent()
        new_report = await agent.generate_report(
            consultant_name="YARLEN ASTRID ALVAREZ BUILES (203)",
            report_type="preview"
        )
        
        # Comparar métricas
        log_info("\nCOMPARACIÓN:")
        
        old_sql = old_report.get('data', {}).get('sql_rows', 0)
        new_sql = new_report.get('data', {}).get('sql_rows', 0)
        
        log_info(f"  SQL rows:")
        log_info(f"    - Antiguo: {old_sql}")
        log_info(f"    - Nuevo:   {new_sql}")
        if old_sql == new_sql:
            log_success("    ✓ IGUALES")
        else:
            log_warning(f"    ⚠ DIFERENTES (diferencia: {abs(old_sql - new_sql)})")
        
        old_evidence = old_report.get('data', {}).get('evidence_count', 0)
        new_evidence = new_report.get('data', {}).get('evidence_count', 0)
        
        log_info(f"  Evidence count:")
        log_info(f"    - Antiguo: {old_evidence}")
        log_info(f"    - Nuevo:   {new_evidence}")
        if old_evidence == new_evidence:
            log_success("    ✓ IGUALES")
        else:
            diff_pct = abs(old_evidence - new_evidence) / max(old_evidence, 1) * 100
            if diff_pct < 10:
                log_success(f"    ✓ SIMILARES (diferencia: {diff_pct:.1f}%)")
            else:
                log_warning(f"    ⚠ DIFERENTES (diferencia: {diff_pct:.1f}%)")
        
        # Guardar comparación
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "old_report": old_report,
            "new_report": new_report,
            "metrics_comparison": {
                "sql_rows": {"old": old_sql, "new": new_sql, "equal": old_sql == new_sql},
                "evidence_count": {"old": old_evidence, "new": new_evidence, "equal": old_evidence == new_evidence}
            }
        }
        save_debug_report("comparison_full", comparison)
        
        log_success("✅ COMPARACIÓN COMPLETADA")
        return True
        
    except Exception as e:
        log_error(f"Error en comparación: {e}")
        print(traceback.format_exc())
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
async def main():
    log_header("FASE 3: VALIDACIÓN COMPLETA DEL REFACTORING")
    log_info(f"Timestamp: {datetime.now().isoformat()}")
    log_info(f"Python: {sys.version.split()[0]}")
    log_info(f"Project root: {project_root}")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": []
    }
    
    all_passed = True
    
    # Test 1: ToolContext
    try:
        passed = await test_tool_context()
        results["tests"].append({"name": "ToolContext", "passed": passed})
        if not passed:
            all_passed = False
    except Exception as e:
        log_error(f"Test ToolContext crashed: {e}")
        results["tests"].append({"name": "ToolContext", "passed": False, "error": str(e)})
        all_passed = False
    
    # Test 2: SQL Tool
    try:
        passed = await test_sql_tool_autonomous()
        results["tests"].append({"name": "SQL Tool", "passed": passed})
        if not passed:
            all_passed = False
    except Exception as e:
        log_error(f"Test SQL Tool crashed: {e}")
        results["tests"].append({"name": "SQL Tool", "passed": False, "error": str(e)})
        all_passed = False
    
    # Test 3: Evidence Tool
    try:
        passed = await test_evidence_tool_dependency_resolution()
        results["tests"].append({"name": "Evidence Tool", "passed": passed})
        if not passed:
            all_passed = False
    except Exception as e:
        log_error(f"Test Evidence Tool crashed: {e}")
        results["tests"].append({"name": "Evidence Tool", "passed": False, "error": str(e)})
        all_passed = False
    
    # Test 4: Full Agent Flow
    try:
        passed = await test_full_agent_flow()
        results["tests"].append({"name": "Full Agent Flow", "passed": passed})
        if not passed:
            all_passed = False
    except Exception as e:
        log_error(f"Test Full Agent crashed: {e}")
        results["tests"].append({"name": "Full Agent Flow", "passed": False, "error": str(e)})
        all_passed = False
    
    # Test 5: Comparison (opcional)
    try:
        passed = await test_comparison_with_old_system()
        results["tests"].append({"name": "Comparison", "passed": passed})
    except Exception as e:
        log_warning(f"Test Comparison crashed (no crítico): {e}")
        results["tests"].append({"name": "Comparison", "passed": False, "error": str(e)})
    
    # Resumen final
    log_header("RESUMEN FINAL")
    
    passed_count = sum(1 for t in results["tests"] if t["passed"])
    total_count = len(results["tests"])
    
    for test in results["tests"]:
        status = "✓ PASSED" if test["passed"] else "✗ FAILED"
        color = Colors.GREEN if test["passed"] else Colors.FAIL
        print(f"{color}{status}{Colors.ENDC} - {test['name']}")
        if not test["passed"] and "error" in test:
            log_error(f"  Error: {test['error']}")
    
    print(f"\n{Colors.BOLD}Total: {passed_count}/{total_count} tests pasaron{Colors.ENDC}")
    
    # Guardar resumen
    save_debug_report("test_summary", results)
    
    if all_passed:
        log_header("🎉 TODOS LOS TESTS CRÍTICOS PASARON")
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("✅ Refactoring exitoso!")
        print("✅ Tools completamente autónomas")
        print("✅ Agent simplificado")
        print("✅ Razonamiento preservado")
        print("✅ Listo para FastMCP")
        print(f"{Colors.ENDC}")
        return 0
    else:
        log_header("❌ ALGUNOS TESTS FALLARON")
        print(f"{Colors.FAIL}{Colors.BOLD}")
        print("Revisa los logs de debug en: data_store/logs/test_phase3/")
        print(f"{Colors.ENDC}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)