"""Punto de entrada del servidor FastMCP para las herramientas de ReportAgent.

Este módulo instancia un servidor FastMCP, registra cada tool con los
modelos de entrada y salida correspondientes y las expone por HTTP.  Se
puede ejecutar mediante la CLI (`fastmcp run server.py:mcp --transport http`)
 o directamente en un entorno local para desarrollo.
"""

from __future__ import annotations

from fastmcp import FastMCP

from .schemas import (
    SQLDataExtractionInput,
    SQLDataExtractionOutput,
    EvidenceRetrievalInput,
    EvidenceRetrievalOutput,
    SummaryGenerationInput,
    SummaryGenerationOutput,
    BusinessRulesInput,
    BusinessRulesOutput,
    RecommendationsInput,
    RecommendationsOutput,
    ChartGenerationInput,
    ChartGenerationOutput,
)

from .tools.sql_extraction import sql_data_extraction
from .tools.evidence import evidence_retrieval
from .tools.summary import summary_generation
from .tools.business_rules import business_rules
from .tools.recommendations import recommendations_generation
from .tools.charts import chart_generation


mcp = FastMCP("Report Tools Server")


@ mcp.tool(name="sql_data_extraction")
async def sql_data_extraction_tool(params: SQLDataExtractionInput) -> SQLDataExtractionOutput:
    """Extraer IDs de defecto y datos crudos para un consultor y tipo.

    Consulta la documentación del modelo `SQLDataExtractionInput` para
    detalles de los parámetros.
    """
    return await sql_data_extraction(params)


@ mcp.tool(name="evidence_retrieval")
async def evidence_retrieval_tool(params: EvidenceRetrievalInput) -> EvidenceRetrievalOutput:
    """Recuperar evidencia para IDs de defecto especificados o derivados del historial."""
    return await evidence_retrieval(params)


@ mcp.tool(name="summary_generation")
async def summary_generation_tool(params: SummaryGenerationInput) -> SummaryGenerationOutput:
    """Generar un resumen en lenguaje natural a partir de una consulta y evidencia opcional."""
    return await summary_generation(params)


@ mcp.tool(name="business_rules")
async def business_rules_tool(params: BusinessRulesInput) -> BusinessRulesOutput:
    """Evaluar reglas de negocio sobre defectos o datos crudos."""
    return await business_rules(params)


@ mcp.tool(name="recommendations_generation")
async def recommendations_generation_tool(params: RecommendationsInput) -> RecommendationsOutput:
    """Generar acciones recomendadas basadas en un resumen o una evidencia."""
    return await recommendations_generation(params)


@ mcp.tool(name="chart_generation")
async def chart_generation_tool(params: ChartGenerationInput) -> ChartGenerationOutput:
    """Generar una descripción de gráfica a partir de datos crudos y el tipo de gráfica."""
    return await chart_generation(params)


if __name__ == "__main__":
    # Cuando se ejecuta directamente, iniciar el servidor HTTP.
    # Durante el desarrollo, esto permite probar las tools manualmente.
    mcp.run(transport="http", host="127.0.0.1", port=8000)
