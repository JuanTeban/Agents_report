"""Implementación de la herramienta de generación de recomendaciones.

Produce recomendaciones simples a partir de un resumen o de una lista de
evidencias.  La función auxiliar `_extract_summary_or_evidence` busca en
el historial el resumen o la evidencia más reciente.
"""

from __future__ import annotations

from typing import List

from ..schemas import (
    RecommendationsInput,
    RecommendationsOutput,
    ToolCallRecord,
)


def _extract_summary_or_evidence(history: List[ToolCallRecord]) -> tuple[str, List[str]]:
    """Extraer resumen o evidencia del historial.

    Recorre el historial de forma inversa y obtiene el resumen y la
    evidencia más recientes disponibles.  Devuelve el resumen (cadena
    vacía si no existe) y la lista de evidencias.
    """
    summary = ""
    evidence: List[str] = []
    for record in reversed(history or []):
        if not summary and record.name == "summary_generation":
            summary = record.result.get("summary") or ""
        if not evidence and record.name == "evidence_retrieval":
            evidence = record.result.get("evidence_list") or []
        if summary and evidence:
            break
    return summary, evidence


async def recommendations_generation(params: RecommendationsInput) -> RecommendationsOutput:
    """Generar recomendaciones a partir de un resumen o una evidencia.

    Si se proporciona un resumen, las recomendaciones se basan en su
    contenido; de lo contrario se utilizan las evidencias.  Si no se
    proporcionan explícitamente, se derivan del historial.
    """
    summary = params.summary or ""
    evidence = params.evidence_list or []

    if (not summary or not evidence) and params.tool_history:
        hist_summary, hist_evidence = _extract_summary_or_evidence(params.tool_history)
        if not summary:
            summary = hist_summary
        if not evidence:
            evidence = hist_evidence

    recommendations: List[str] = []

    if summary:
        recommendations.append("Revisar los puntos clave del resumen para priorizar acciones.")
        recommendations.append("Preparar un plan de mejora basado en los hallazgos del resumen.")
    elif evidence:
        recommendations.append("Analizar detalladamente la evidencia recopilada.")
        recommendations.append("Derivar conclusiones y posibles acciones a partir de la evidencia.")
    else:
        recommendations.append("Sin información suficiente para generar recomendaciones.")

    return RecommendationsOutput(recommendations=recommendations)
