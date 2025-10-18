"""Implementación de la herramienta de generación de resúmenes.

Genera un resumen en lenguaje natural a partir de una consulta y
opcionalmente evidencia extraída del historial.  La lógica de
resumen real debería delegarse a un modelo de lenguaje o servicio.
"""

from __future__ import annotations

from typing import List

from ..schemas import (
    SummaryGenerationInput,
    SummaryGenerationOutput,
    ToolCallRecord,
)


def _extract_evidence_from_history(history: List[ToolCallRecord]) -> List[str]:
    """Extraer evidencia del historial.

    Busca en los registros históricos cualquier `evidence_list` devuelto
    por `evidence_retrieval` y los concatena.  No elimina duplicados para
    preservar contexto.
    """

    evidences: List[str] = []
    for record in history or []:
        if record.name == "evidence_retrieval":
            ev_list = record.result.get("evidence_list") or []
            evidences.extend(ev_list)
    return evidences


async def summary_generation(params: SummaryGenerationInput) -> SummaryGenerationOutput:
    """Generar un resumen a partir de una consulta y evidencia opcional.

    Combina la consulta con la evidencia extraída del historial (si
    existe) y devuelve un texto resumido.  Esta función debería
    invocar un modelo de lenguaje en un escenario real.
    """

    evidence_list: List[str] = []
    if params.tool_history:
        evidence_list = _extract_evidence_from_history(params.tool_history)

    # Componemos el texto de entrada
    if evidence_list:
        combined_text = params.query + "\n\nEvidencia:\n" + "\n".join(evidence_list)
    else:
        combined_text = params.query

    # Resumen de ejemplo
    summary_text = f"Resumen generado para la pregunta: {params.query}."
    if evidence_list:
        summary_text += f" Se consideró {len(evidence_list)} elemento(s) de evidencia."

    return SummaryGenerationOutput(summary=summary_text)