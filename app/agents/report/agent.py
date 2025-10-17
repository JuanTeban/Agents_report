# app/agents/report/agent.py (REEMPLAZAR COMPLETO)

from typing import Dict, Any
from datetime import datetime

from app.agents.core import BaseAgent, AgentMessage
from app.tools.core import ToolRegistry
from .config import REPORT_AGENT_INSTRUCTIONS, RESPONSE_FORMAT_INSTRUCTIONS

class ReportAgent(BaseAgent):
    """
    Agente especializado en generación de reportes.
    
    **REFACTORIZADO**: Ya no contiene lógica de preparación de datos.
    Las Tools son completamente autónomas y resuelven sus propias dependencias.
    
    El rol del Agent se reduce a:
    1. Razonamiento estratégico (decidir qué hacer)
    2. Orquestación del flujo
    3. Compilación del reporte final
    """
    
    def __init__(self):
        tools = [
            ToolRegistry.get("sql_data_extraction"),
            ToolRegistry.get("evidence_retrieval"),
            ToolRegistry.get("business_rules"),
            ToolRegistry.get("summary_generation"),
            ToolRegistry.get("recommendations_generation"),
            ToolRegistry.get("chart_generation")
        ]
        
        tools = [t for t in tools if t is not None]
        
        super().__init__(
            name="ReportAgent",
            tools=tools,
            max_iterations=15,
            response_format_instructions=RESPONSE_FORMAT_INSTRUCTIONS
        )
        
        self.agent_instructions = REPORT_AGENT_INSTRUCTIONS
    
    # NO MORE _execute_tool override!
    # NO MORE _enrich_tool_args_smart!
    # Las Tools son autónomas ahora.
    
    async def process_task(self, task: str, context: Dict[str, Any]) -> AgentMessage:
        """
        Genera reporte completo para un consultor.
        
        SIMPLIFICADO: Solo valida contexto y delega a run().
        """
        consultant_name = context.get("consultant_name")
        report_type = context.get("report_type", "preview")
        
        if not consultant_name:
            return AgentMessage(
                sender=self.name,
                content="Error: consultant_name es requerido",
                metadata={"error": "missing_consultant_name"},
                success=False
            )
        
        task_description = (
            f"Genera un reporte completo tipo '{report_type}' para el consultor: {consultant_name}. "
            f"Usa las tools disponibles de forma inteligente para obtener "
            f"datos SQL, evidencia, reglas de negocio, generar análisis y gráficos."
        )
        
        return await self.run(task_description, context)
    
    async def generate_report(
        self,
        consultant_name: str,
        report_type: str = "preview"
    ) -> Dict[str, Any]:
        """Interfaz compatible con ReportEngine"""
        context = {
            "consultant_name": consultant_name,
            "report_type": report_type
        }
        
        result = await self.process_task(
            task=f"Generar reporte para {consultant_name}",
            context=context
        )
        
        if not result.success:
            return self._error_report(consultant_name, result.content)
        
        # Compile from ToolContext
        final_context = result.metadata.get("context", context)
        return self._compile_report(consultant_name, report_type, final_context)
    
    def _compile_report(
        self,
        consultant_name: str,
        report_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compila reporte desde historial.
        
        NOTA: Esta lógica podría también moverse a una Tool dedicada
        "report_compilation" si queremos máxima modularidad.
        """
        tool_history = context.get("tool_history", [])
        
        sql_data = []
        evidence_count = 0
        summary = ""
        recommendations = ""
        charts = {}
        
        for entry in tool_history:
            result = entry.get("result", {})
            if not result.get("success"):
                continue
            
            tool_name = entry.get("tool")
            data = result.get("data")
            
            if tool_name == "sql_data_extraction":
                sql_data = data or []
                self.logger.log_info(f"✓ SQL data compilado: {len(sql_data)} filas")
            
            elif tool_name == "evidence_retrieval":
                if data:
                    for sections in data.values():
                        evidence_count += sum(len(chunks) for chunks in sections.values())
                self.logger.log_info(f"✓ Evidencia compilada: {evidence_count} chunks")
            
            elif tool_name == "summary_generation":
                summary = data or ""
                self.logger.log_info(f"✓ Summary compilado: {len(summary)} chars")
            
            elif tool_name == "recommendations_generation":
                recommendations = data or ""
                self.logger.log_info(f"✓ Recommendations compiladas: {len(recommendations)} chars")
            
            elif tool_name == "chart_generation":
                charts = data or {}
                self.logger.log_info(f"✓ Charts compilados: {len(charts)} gráficos")
        
        return {
            "consultant": consultant_name,
            "generated_at": datetime.now().isoformat(),
            "type": report_type,
            "data": {
                "sql_rows": len(sql_data),
                "evidence_count": evidence_count
            },
            "sections": {
                "summary": summary,
                "recommendations": recommendations
            },
            "charts": charts,
            "metadata": {
                "version": "3.0-autonomous-tools",
                "agent": self.name,
                "architecture": "dependency-injection"
            }
        }
    
    def _error_report(self, consultant_name: str, error: str) -> Dict[str, Any]:
        """Reporte de error"""
        return {
            "consultant": consultant_name,
            "generated_at": datetime.now().isoformat(),
            "type": "error",
            "data": {"sql_rows": 0, "evidence_count": 0},
            "sections": {
                "summary": f"Error: {error}",
                "recommendations": "No disponible"
            },
            "charts": {},
            "metadata": {
                "version": "3.0-autonomous-tools",
                "error": error
            }
        }