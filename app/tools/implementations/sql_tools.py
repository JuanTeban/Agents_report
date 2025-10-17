# app/tools/implementations/sql_tools.py (REEMPLAZAR COMPLETO)

import json
import re
from pydantic import Field
from typing import List, Dict, Any

from app.tools.core import BaseTool, ToolInput, ToolOutput, register_tool, ToolContext
from app.core.report.retrieval import ReportGeneratorRetriever
from app.core.ia.llm import get_llm_provider
from app.core.report.prompts import ReportGeneratorPromptManager
from app.tools.tools import execute_duckdb_query

@register_tool
class SqlDataExtractionTool(BaseTool):
    """
    Extrae datos SQL de un consultor.
    
    **Autonomía**: No tiene dependencias, solo necesita consultant_name.
    """
    
    class Input(ToolInput):
        consultant_name: str = Field(
            ...,
            description="Nombre completo del consultor responsable"
        )
    
    @property
    def name(self) -> str:
        return "sql_data_extraction"
    
    @property
    def description(self) -> str:
        return (
            "Ejecuta consulta SQL para extraer TODOS los datos "
            "de defectos asignados a un consultor desde DuckDB"
        )
    
    @property
    def input_schema(self) -> type[ToolInput]:
        return self.Input
    
    @property
    def dependencies(self) -> List[str]:
        return []  # No dependencies
    
    def __init__(self):
        self.retriever = ReportGeneratorRetriever()
        self.llm = get_llm_provider()
        self.prompt_manager = ReportGeneratorPromptManager()
    
    async def _execute_impl(self, consultant_name: str) -> ToolOutput:
        """Lógica de extracción SQL"""
        try:
            # 1. Get schema context
            schema_context = await self.retriever.get_schema_context(
                f"datos del consultor {consultant_name}"
            )
            
            if not schema_context:
                return ToolOutput(
                    success=False,
                    error="No se encontró contexto de esquema"
                )
            
            # 2. Generate SQL
            prompt = self._build_sql_prompt(consultant_name, schema_context)
            sql_response = await self.llm.generate_async(prompt)
            sql = self._clean_sql(sql_response.content)
            sql = self._ensure_no_limit(sql)
            
            # 3. Execute query
            result = execute_duckdb_query.invoke({"sql_query": sql})
            data = json.loads(result)
            
            if "json_data" in data and data["json_data"]:
                return ToolOutput(
                    success=True,
                    data=data["json_data"],
                    metadata={
                        "row_count": len(data["json_data"]),
                        "sql_executed": sql,
                        "consultant": consultant_name
                    }
                )
            else:
                return ToolOutput(
                    success=False,
                    data=[],
                    error=f"No se encontraron datos para: {consultant_name}",
                    metadata={"sql_executed": sql}
                )
                
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"Error en extracción SQL: {str(e)}"
            )
    
    def _build_sql_prompt(self, consultant_name: str, schema_context: List[Dict]) -> str:
        """Construye prompt para generación SQL"""
        context_str = "\n".join([doc.get("content", "") for doc in schema_context])
        
        return f"""Eres un experto en SQL y DuckDB. Devuelve UNA sola consulta SQL ejecutable.

REGLAS DURAS (OBLIGATORIAS):
1) Filtro por responsable (texto libre): usa obligatoriamente:
   UPPER(responsable_del_defecto) LIKE UPPER('%{consultant_name}%')
2) Orden: como texto numérico convertido a número:
   ORDER BY CAST(REPLACE(antiguedad_del_defecto_promedio_en_dias, ',', '.') AS DECIMAL) DESC
3) NO USES alias ni cambies nombres de columnas o tablas.
4) Devuelve SOLO el SQL (sin ``` ni explicaciones), finalizando con ';'.

CONTEXTO DE TABLAS:
{context_str}

NECESIDAD:
Extraer TODOS los datos de defectos de "{consultant_name}"

CONSULTA SQL:"""
    
    def _clean_sql(self, sql: str) -> str:
        """Limpia respuesta SQL del LLM"""
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*$', '', sql)
        sql = sql.strip()
        if not sql.endswith(';'):
            sql += ';'
        return sql
    
    def _ensure_no_limit(self, sql: str) -> str:
        """Asegura que no haya LIMIT en la query"""
        return re.sub(r'\s+LIMIT\s+\d+', '', sql, flags=re.IGNORECASE)