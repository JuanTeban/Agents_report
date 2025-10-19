"""Agente especializado en generación de reportes usando tools remotas FastMCP."""

from typing import Dict, Any, List
from datetime import datetime
import re
import os

from app.agents.core import BaseAgent, AgentMessage
from app.agents.core.mcp_client import MCPClient
from .config import REPORT_AGENT_INSTRUCTIONS, RESPONSE_FORMAT_INSTRUCTIONS


class ReportAgent(BaseAgent):
    """Agente para generar reportes completos de defectos.
    
    Utiliza exclusivamente tools remotas vía FastMCP para:
    - Extraer datos SQL
    - Recuperar evidencia multimodal
    - Obtener reglas de negocio
    - Generar análisis (resumen, recomendaciones)
    - Crear gráficos
    """
    
    def __init__(self, mcp_client: MCPClient | None = None):
        """Inicializa el ReportAgent.
        
        Args:
            mcp_client: Cliente MCP. Si None, se crea uno nuevo desde FASTMCP_URL.
        """
        # Crear cliente MCP si no se proporciona
        if mcp_client is None:
            fastmcp_url = os.environ.get("FASTMCP_URL", "http://localhost:8000")
            mcp_client = MCPClient(base_url=fastmcp_url)
        
        super().__init__(
            name="ReportAgent",
            mcp_client=mcp_client,
            max_iterations=15,
            response_format_instructions=RESPONSE_FORMAT_INSTRUCTIONS
        )
        
        self.agent_instructions = REPORT_AGENT_INSTRUCTIONS
    
    async def process_task(self, task: str, context: Dict[str, Any]) -> AgentMessage:
        """Genera reporte completo para un consultor.
        
        Args:
            task: Descripción de la tarea
            context: Debe contener:
                - consultant_name: str
                - report_type: str (opcional, default='preview')
        
        Returns:
            AgentMessage con el resultado
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
        """Interfaz pública para generar reportes (compatibilidad).
        
        Args:
            consultant_name: Nombre del consultor
            report_type: Tipo de reporte (preview/final)
            
        Returns:
            Diccionario con el reporte completo
        """
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
        
        final_context = result.metadata.get("context", context)
        return self._compile_report(consultant_name, report_type, final_context)
    
    async def _execute_tool(self, tool_name: str, tool_args: Dict) -> Any:
        """Override para enriquecer argumentos automáticamente.
        
        CRÍTICO: NO usar datos del LLM, usar datos REALES del historial.
        """
        # Enriquecer args antes de ejecutar
        tool_args = await self._enrich_tool_args_smart(tool_name, tool_args)
        
        self.logger.log_info(
            f"✓ Args finales para {tool_name}",
            {"args_final": self._safe_preview(tool_args)}
        )
        
        # Ejecutar vía BaseAgent (que usa MCPClient)
        return await super()._execute_tool(tool_name, tool_args)
    
    async def _enrich_tool_args_smart(
        self,
        tool_name: str,
        tool_args: Dict
    ) -> Dict:
        """Enriquece argumentos de tools con datos del historial.
        
        ESTRATEGIA:
        1. Para tools de análisis (summary, recommendations, charts):
           - IGNORAR lo que pasa el LLM
           - OBTENER datos reales del historial
        2. Para otras tools:
           - Solo completar parámetros faltantes
        """
        context = self._current_run_context
        tool_history = context.get("tool_history", [])
        
        self.logger.log_info(
            f"Enriqueciendo tool: {tool_name}",
            {
                "args_llm": tool_args,
                "tool_history_count": len(tool_history)
            }
        )
        
        # SQL Data Extraction
        if tool_name == "sql_data_extraction":
            if "consultant_name" not in tool_args:
                tool_args["consultant_name"] = context.get("consultant_name")
        
        # Evidence Retrieval
        elif tool_name == "evidence_retrieval":
            # Extraer defect_ids del SQL si no vienen
            if "defect_ids" not in tool_args or not tool_args["defect_ids"]:
                sql_result = self._find_tool_result(tool_history, "sql_data_extraction")
                if sql_result and sql_result.get("success"):
                    sql_data = sql_result.get("data", [])
                    if sql_data:
                        extracted_ids = self._extract_defect_ids(sql_data)
                        tool_args["defect_ids"] = extracted_ids
                        self.logger.log_info(
                            f"Defect IDs extraídos del SQL: {len(extracted_ids)}",
                            {"ids": extracted_ids}
                        )
            
            if "consultant_name" not in tool_args:
                tool_args["consultant_name"] = context.get("consultant_name")
        
        # Business Rules
        elif tool_name == "business_rules":
            if "query" not in tool_args or not tool_args["query"]:
                sql_result = self._find_tool_result(tool_history, "sql_data_extraction")
                if sql_result and sql_result.get("success"):
                    sql_data = sql_result.get("data", [])
                    tool_args["query"] = self._build_context_query(sql_data)
            
            if "top_k" not in tool_args:
                tool_args["top_k"] = 5
        
        # Summary/Recommendations Generation
        elif tool_name in ["summary_generation", "recommendations_generation"]:
            # Obtener SQL data del historial
            sql_result = self._find_tool_result(tool_history, "sql_data_extraction")
            if sql_result and sql_result.get("success"):
                tool_args["sql_data"] = sql_result.get("data", [])
                self.logger.log_info(
                    f"✓ Usando {len(tool_args['sql_data'])} filas reales para {tool_name}"
                )
            else:
                tool_args["sql_data"] = []
                self.logger.log_warning(f"⚠️ No hay datos SQL disponibles para {tool_name}")
            
            # Construir RAG context desde evidencia y reglas
            evidence_result = self._find_tool_result(tool_history, "evidence_retrieval")
            rules_result = self._find_tool_result(tool_history, "business_rules")
            
            tool_args["rag_context"] = {
                "evidence_by_defect": (
                    evidence_result.get("data", {})
                    if evidence_result and evidence_result.get("success")
                    else {}
                ),
                "business_rules": (
                    rules_result.get("data", [])
                    if rules_result and rules_result.get("success")
                    else []
                ),
                "schemas": []
            }
            
            if "consultant_name" not in tool_args:
                tool_args["consultant_name"] = context.get("consultant_name")
        
        # Chart Generation
        elif tool_name == "chart_generation":
            sql_result = self._find_tool_result(tool_history, "sql_data_extraction")
            if sql_result and sql_result.get("success"):
                tool_args["sql_data"] = sql_result.get("data", [])
                self.logger.log_info(
                    f"Usando {len(tool_args['sql_data'])} filas reales para gráficos"
                )
            else:
                tool_args["sql_data"] = []
        
        return tool_args
    
    def _find_tool_result(self, tool_history: List[Dict], tool_name: str) -> Dict:
        """Busca resultado de una tool en el historial."""
        for entry in reversed(tool_history):
            if entry.get("tool") == tool_name:
                return entry.get("result", {})
        return {}
    
    def _safe_preview(self, data: Any, max_len: int = 100) -> Any:
        """Preview seguro para logging."""
        if isinstance(data, list) and len(data) > 0:
            return f"[{len(data)} items]"
        elif isinstance(data, dict):
            keys = list(data.keys())[:5]
            return f"{{keys: {keys}, ...}}"
        else:
            return str(data)[:max_len]
    
    def _compile_report(
        self,
        consultant_name: str,
        report_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compila reporte desde historial de tools."""
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
                self.logger.log_info(f"✓ SQL data: {len(sql_data)} filas")
            
            elif tool_name == "evidence_retrieval":
                if data:
                    for sections in data.values():
                        if isinstance(sections, dict):
                            evidence_count += sum(
                                len(chunks) for chunks in sections.values()
                                if isinstance(chunks, list)
                            )
                self.logger.log_info(f"✓ Evidencia: {evidence_count} chunks")
            
            elif tool_name == "summary_generation":
                summary = data or ""
                self.logger.log_info(f"✓ Summary: {len(summary)} chars")
            
            elif tool_name == "recommendations_generation":
                recommendations = data or ""
                self.logger.log_info(f"✓ Recommendations: {len(recommendations)} chars")
            
            elif tool_name == "chart_generation":
                charts = data or {}
                self.logger.log_info(f"✓ Charts: {len(charts)} gráficos")
        
        report = {
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
                "version": "3.0-fastmcp",
                "agent": self.name,
                "mcp_url": self.mcp_client.base_url if self.mcp_client else None
            }
        }
        
        self.logger.log_info("📋 Reporte compilado", {
            "sql_rows": len(sql_data),
            "evidence_count": evidence_count,
            "charts": len(charts)
        })
        
        return report
    
    def _error_report(self, consultant_name: str, error: str) -> Dict[str, Any]:
        """Reporte de error."""
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
                "version": "3.0-fastmcp",
                "error": error
            }
        }
    
    def _extract_defect_ids(self, sql_data: List[Dict]) -> List[str]:
        """Extrae IDs de defectos del SQL data."""
        if not sql_data:
            return []
        
        ids = set()
        for row in sql_data:
            defect_col = row.get("defectos", "")
            defect_str = str(defect_col)
            match = re.search(r'\b(\d{6,})\b', defect_str)
            if match:
                ids.add(match.group(1))
        
        return list(ids)
    
    def _build_context_query(self, sql_data: List[Dict]) -> str:
        """Construye query para business rules desde SQL data."""
        if not sql_data:
            return ""
        
        terms = set()
        for row in sql_data:
            if "modulo" in row:
                modulo = str(row["modulo"]).lower()
                if modulo and modulo != "nan":
                    terms.add(modulo)
            
            if "categoria_de_defecto" in row:
                categoria = str(row["categoria_de_defecto"]).lower()
                if categoria and categoria != "nan":
                    terms.add(categoria)
        
        return " ".join(terms)