"""Implementación de la herramienta de recuperación de evidencia.

Esta herramienta obtiene evidencias para un conjunto de IDs de defecto.
Incluye una función auxiliar que extrae IDs del historial de herramientas
cuando no se proporcionan explícitamente.
"""

from __future__ import annotations

from typing import List, Optional

from ..schemas import (
    EvidenceRetrievalInput,
    EvidenceRetrievalOutput,
    ToolCallRecord,
)


def _extract_defect_ids_from_history(history: List[ToolCallRecord]) -> List[str]:
    """Extraer IDs de defecto del historial.

    Itera sobre los registros históricos y concatena los `defect_ids`
    devueltos por la herramienta `sql_data_extraction`.  Quita
    duplicados preservando el orden.

    Args:
        history: Lista de registros históricos.

    Returns:
        Lista de IDs únicos de defecto.
    """

    seen: set[str] = set()
    extracted: List[str] = []
    for record in history or []:
        if record.name == "sql_data_extraction":
            defect_ids = record.result.get("defect_ids") or []
            for d_id in defect_ids:
                if d_id not in seen:
                    seen.add(d_id)
                    extracted.append(d_id)
    return extracted


async def evidence_retrieval(params: EvidenceRetrievalInput) -> EvidenceRetrievalOutput:
    """Recuperar evidencia para un conjunto de IDs de defecto.

    Primero resuelve la lista de defectos: usa `params.defect_ids` si se
    proporciona o, en caso contrario, intenta derivarla del historial.
    Después genera evidencia ficticia para cada ID.

    Args:
        params: Instancia de `EvidenceRetrievalInput` con IDs de defecto y/o
            historial.

    Returns:
        `EvidenceRetrievalOutput` con la lista de evidencias y notas opcionales.
    """

    defect_ids: List[str] = []
    if params.defect_ids:
        defect_ids = params.defect_ids
    elif params.tool_history:
        defect_ids = _extract_defect_ids_from_history(params.tool_history)

    # Si no hay IDs, devolvemos una nota
    if not defect_ids:
        return EvidenceRetrievalOutput(
            evidence_list=[],
            notes="No se proporcionaron defectos ni se encontraron en el historial.",
        )

    # Generamos evidencia ficticia
    evidence_list: List[str] = [f"Evidencia del defecto {d}" for d in defect_ids]

    return EvidenceRetrievalOutput(evidence_list=evidence_list)
