#!/usr/bin/env python3
"""
Test Fase 3 - FLUJO REAL DEL AGENT
Prueba el flujo completo pasando por el LLM igual que generate_report_v2.py
Con logs super detallados para ver qué está pasando el LLM
"""
import asyncio
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import app.tools.implementations
from app.agents.report.agent import ReportAgent

# Colors
class C:
    H = '\033[95m'; B = '\033[94m'; G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'; E = '\033[0m'; BOLD = '\033[1m'

def log(msg, color=C.E): print(f"{color}{msg}{C.E}")

async def test_agent_with_llm_monitoring():
    """
    Test que emula exactamente lo que hace generate_report_v2.py
    pero con monitoring detallado de cada decisión del LLM
    """
    log("\n" + "="*100, C.H + C.BOLD)
    log("TEST: FLUJO COMPLETO DEL AGENT CON LLM MONITORING", C.H + C.BOLD)
    log("="*100 + "\n", C.H + C.BOLD)
    
    consultant = "YARLEN ASTRID ALVAREZ BUILES (203)"
    
    try:
        log("🤖 Inicializando ReportAgent...", C.B)
        agent = ReportAgent()
        
        # Verificar configuración
        log(f"✓ Agent inicializado", C.G)
        log(f"  - Tools: {list(agent.tools.keys())}", C.B)
        log(f"  - Max iterations: {agent.max_iterations}", C.B)
        
        # Verificar instrucciones
        log(f"\n📋 Verificando instrucciones del agent:", C.B)
        if hasattr(agent, 'agent_instructions'):
            preview = agent.agent_instructions[:200] + "..."
            log(f"  - Agent instructions: {preview}", C.B)
        
        if hasattr(agent, 'response_format_instructions'):
            preview = agent.response_format_instructions[:300] + "..."
            log(f"  - Response format: {preview}", C.B)
        
        # Hook para interceptar llamadas a tools
        original_execute_tool = agent._execute_tool
        tool_calls_log = []
        
        async def monitored_execute_tool(tool_name: str, tool_args: dict):
            log(f"\n{'='*80}", C.Y)
            log(f"🔧 LLAMADA A TOOL: {tool_name}", C.Y + C.BOLD)
            log(f"{'='*80}", C.Y)
            log(f"📥 Args recibidos del LLM:", C.Y)
            log(json.dumps(tool_args, indent=2, ensure_ascii=False), C.Y)
            
            # Registrar
            call_info = {
                "tool": tool_name,
                "args_from_llm": tool_args.copy(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Ejecutar
            result = await original_execute_tool(tool_name, tool_args)
            
            call_info["result"] = {
                "success": result.success,
                "error": result.error,
                "metadata": result.metadata
            }
            tool_calls_log.append(call_info)
            
            log(f"\n📤 Resultado:", C.Y)
            log(f"  - Success: {result.success}", C.G if result.success else C.R)
            if result.error:
                log(f"  - Error: {result.error}", C.R)
            if result.metadata:
                log(f"  - Metadata: {json.dumps(result.metadata, indent=2)}", C.B)
            log(f"{'='*80}\n", C.Y)
            
            return result
        
        # Reemplazar temporalmente
        agent._execute_tool = monitored_execute_tool
        
        # Ejecutar generación de reporte
        log(f"\n🚀 Iniciando generación de reporte para: {consultant}", C.H + C.BOLD)
        log(f"{'='*100}\n", C.H)
        
        report = await agent.generate_report(
            consultant_name=consultant,
            report_type="preview"
        )
        
        # Análisis de resultados
        log(f"\n{'='*100}", C.H + C.BOLD)
        log("📊 RESULTADOS DEL REPORTE", C.H + C.BOLD)
        log(f"{'='*100}\n", C.H)
        
        log(f"✓ Consultor: {report.get('consultant')}", C.G)
        log(f"✓ Fecha: {report.get('generated_at')}", C.G)
        log(f"✓ SQL rows: {report['data']['sql_rows']}", C.G)
        log(f"✓ Evidence count: {report['data']['evidence_count']}", C.G)
        log(f"✓ Charts: {len(report.get('charts', {}))}", C.G)
        log(f"✓ Arquitectura: {report['metadata'].get('architecture')}", C.G)
        
        # Análisis de llamadas a tools
        log(f"\n{'='*100}", C.B + C.BOLD)
        log(f"🔍 ANÁLISIS DE LLAMADAS A TOOLS ({len(tool_calls_log)} llamadas)", C.B + C.BOLD)
        log(f"{'='*100}\n", C.B)
        
        for i, call in enumerate(tool_calls_log, 1):
            log(f"\n--- Llamada #{i}: {call['tool']} ---", C.B + C.BOLD)
            
            # Verificar problemas comunes
            args = call['args_from_llm']
            tool = call['tool']
            problems = []
            
            if tool == "evidence_retrieval":
                if "defect_ids" in args:
                    val = args["defect_ids"]
                    if isinstance(val, str):
                        problems.append(f"⚠️  defect_ids es string: '{val}' (debería ser [])")
                    elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], str):
                        if "auto-resuelto" in val[0].lower():
                            problems.append(f"⚠️  defect_ids contiene string descriptivo: {val}")
            
            if tool in ["summary_generation", "recommendations_generation"]:
                if "sql_data" in args:
                    val = args["sql_data"]
                    if isinstance(val, str):
                        problems.append(f"⚠️  sql_data es string: '{val}' (debería ser [])")
                
                if "rag_context" in args:
                    val = args["rag_context"]
                    if isinstance(val, str):
                        problems.append(f"⚠️  rag_context es string: '{val}' (debería ser {{}})")
            
            if problems:
                for p in problems:
                    log(p, C.R)
            else:
                log("✓ Args correctos", C.G)
            
            log(f"Resultado: {'✓ Success' if call['result']['success'] else '✗ Failed'}", 
                C.G if call['result']['success'] else C.R)
            
            if call['result']['error']:
                log(f"Error: {call['result']['error']}", C.R)
        
        # Guardar logs detallados
        debug_dir = Path("data_store/logs/test_agent_llm")
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Log de llamadas
        with open(debug_dir / f"tool_calls_{timestamp}.json", 'w') as f:
            json.dump(tool_calls_log, f, indent=2, ensure_ascii=False)
        
        # Reporte completo
        with open(debug_dir / f"report_{timestamp}.json", 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        log(f"\n📁 Logs guardados en: {debug_dir}", C.B)
        
        # Determinar éxito
        success = report['data']['sql_rows'] > 0
        
        if success:
            log(f"\n{'='*100}", C.G + C.BOLD)
            log("✅ TEST PASADO - Reporte generado exitosamente", C.G + C.BOLD)
            log(f"{'='*100}\n", C.G)
        else:
            log(f"\n{'='*100}", C.R + C.BOLD)
            log("⚠️  TEST PARCIAL - Reporte generado pero sin datos", C.Y + C.BOLD)
            log(f"{'='*100}\n", C.R)
        
        return success
        
    except Exception as e:
        log(f"\n{'='*100}", C.R + C.BOLD)
        log(f"❌ ERROR EN TEST: {e}", C.R + C.BOLD)
        log(f"{'='*100}\n", C.R)
        print(traceback.format_exc())
        return False


async def main():
    log("\n" + "="*100, C.H + C.BOLD)
    log("FASE 3: TEST DE FLUJO REAL DEL AGENT CON LLM", C.H + C.BOLD)
    log("="*100, C.H + C.BOLD)
    log(f"Timestamp: {datetime.now().isoformat()}", C.B)
    log(f"Python: {sys.version.split()[0]}", C.B)
    log("="*100 + "\n", C.H)
    
    success = await test_agent_with_llm_monitoring()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)