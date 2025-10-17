<<<<<<< HEAD
# app/tools/implementations/sql_tools.py (REEMPLAZAR COMPLETO)

=======
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
import json
import re
from pydantic import Field
from typing import List, Dict, Any

<<<<<<< HEAD
from app.tools.core import BaseTool, ToolInput, ToolOutput, register_tool, ToolContext
=======
from app.tools.core import BaseTool, ToolInput, ToolOutput, register_tool
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
from app.core.report.retrieval import ReportGeneratorRetriever
from app.core.ia.llm import get_llm_provider
from app.core.report.prompts import ReportGeneratorPromptManager
from app.tools.tools import execute_duckdb_query

@register_tool
class SqlDataExtractionTool(BaseTool):
    """
    Extrae datos SQL de un consultor.
<<<<<<< HEAD
    
    **Autonomía**: No tiene dependencias, solo necesita consultant_name.
=======
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
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
<<<<<<< HEAD
            "Ejecuta consulta SQL para extraer TODOS los datos "
            "de defectos asignados a un consultor desde DuckDB"
=======
            "Ejecuta consulta SQL optimizada para extraer TODOS los datos "
            "de defectos asignados a un consultor específico desde DuckDB"
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
        )
    
    @property
    def input_schema(self) -> type[ToolInput]:
        return self.Input
    
<<<<<<< HEAD
    @property
    def dependencies(self) -> List[str]:
        return []  # No dependencies
    
=======
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
    def __init__(self):
        self.retriever = ReportGeneratorRetriever()
        self.llm = get_llm_provider()
        self.prompt_manager = ReportGeneratorPromptManager()
    
<<<<<<< HEAD
    async def _execute_impl(self, consultant_name: str) -> ToolOutput:
        """Lógica de extracción SQL"""
        try:
            # 1. Get schema context
=======
    async def execute(self, consultant_name: str) -> ToolOutput:
        """
        Ejecuta extracción SQL.
        
        Returns:
            ToolOutput con json_data, row_count, sql_executed
        """
        try:
            # 1. Obtener contexto de esquema
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
            schema_context = await self.retriever.get_schema_context(
                f"datos del consultor {consultant_name}"
            )
            
            if not schema_context:
                return ToolOutput(
                    success=False,
<<<<<<< HEAD
                    error="No se encontró contexto de esquema"
                )
            
            # 2. Generate SQL
            prompt = self._build_sql_prompt(consultant_name, schema_context)
            sql_response = await self.llm.generate_async(prompt)
            sql = self._clean_sql(sql_response.content)
            sql = self._ensure_no_limit(sql)
            
            # 3. Execute query
=======
                    data=None,
                    error="No se encontró contexto de esquema en la base de datos"
                )
            
            # 2. Generar SQL con LLM - PROMPT MEJORADO
            prompt = self._build_sql_prompt(consultant_name, schema_context)
            
            sql_response = await self.llm.generate_async(prompt)
            
            # 3. Limpiar SQL
            sql = self._clean_sql(sql_response.content)
            
            print(f"\n{'='*80}")
            print(f"SQL GENERADO POR LLM:")
            print(sql)
            print(f"{'='*80}\n")
            # 4. VALIDAR que no tenga LIMIT
            sql = self._ensure_no_limit(sql)


            
            # 5. Ejecutar consulta
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
            result = execute_duckdb_query.invoke({"sql_query": sql})
            data = json.loads(result)
            
            if "json_data" in data and data["json_data"]:
<<<<<<< HEAD
=======
                row_count = len(data["json_data"])
                print(f"✓ SQL extrajo {row_count} filas para {consultant_name}")
                
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
                return ToolOutput(
                    success=True,
                    data=data["json_data"],
                    metadata={
<<<<<<< HEAD
                        "row_count": len(data["json_data"]),
=======
                        "row_count": row_count,
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
                        "sql_executed": sql,
                        "consultant": consultant_name
                    }
                )
            else:
                return ToolOutput(
                    success=False,
                    data=[],
<<<<<<< HEAD
                    error=f"No se encontraron datos para: {consultant_name}",
=======
                    error=f"No se encontraron datos para el consultor: {consultant_name}",
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
                    metadata={"sql_executed": sql}
                )
                
        except Exception as e:
            return ToolOutput(
                success=False,
<<<<<<< HEAD
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
=======
                data=None,
                error=f"Error en extracción SQL: {str(e)}"
            )
    
    def _build_sql_prompt(self, consultant_name: str, schema_context: str) -> str:
        """Construye prompt específico sin usar PromptManager"""
        return f"""Eres un experto en SQL y DuckDB. Devuelve UNA sola consulta SQL ejecutable.

REGLAS CRÍTICAS:
1) Filtro por responsable: usa UPPER(responsable_del_defecto) LIKE UPPER('%{consultant_name}%')
2) NUNCA uses LIMIT - queremos TODOS los registros del consultor
3) Ordena por antigüedad descendente: ORDER BY CAST(REPLACE(antiguedad_del_defecto_promedio_en_dias, ',', '.') AS FLOAT) DESC
4) Devuelve SOLO el SQL, sin explicaciones

ESQUEMA:
{schema_context}

TAREA: 
Genera SQL que extraiga TODOS los defectos de "{consultant_name}" sin límite de filas.

SQL:"""
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
    
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
<<<<<<< HEAD
        return re.sub(r'\s+LIMIT\s+\d+', '', sql, flags=re.IGNORECASE)
=======
        # Remover cualquier LIMIT que el LLM haya agregado
        sql = re.sub(r'\s+LIMIT\s+\d+', '', sql, flags=re.IGNORECASE)
        return sql
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
