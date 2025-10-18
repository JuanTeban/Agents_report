"""Implementación de la herramienta de reglas de negocio.

Evalúa reglas sencillas sobre los defectos o los datos crudos.  En este
ejemplo, se marca un defecto como de alto valor si su campo `value`
excede un umbral.  La función auxiliar `_derive_inputs_from_history`
combina los resultados de `sql_data_extraction` del historial.
"""

from __future__ import annotations

from typing import List, Dict, Any

from ..schemas import (
    BusinessRulesInput,
    BusinessRulesOutput,
    ToolCallRecord,
)


def _derive_inputs_from_history(history: List[ToolCallRecord]) -> tuple[List[str], List[Dict[str, Any]]]:
    """Derivar defect_ids y raw_data del historial.

    Busca resultados de `sql_data_extraction` en el historial y concatena
    los IDs y los datos.  Devuelve un par `(defect_ids, raw_data)`.
    """

    defect_ids: List[str] = []
    raw_data: List[Dict[str, Any]] = []
    for record in history or []:
        if record.name == "sql_data_extraction":
            defect_ids.extend(record.result.get("defect_ids") or [])
            raw_data.extend(record.result.get("raw_data") or [])
    return defect_ids, raw_data


async def business_rules(params: BusinessRulesInput) -> BusinessRulesOutput:
    """Evaluar reglas de negocio sobre defectos o datos crudos.

    Esta implementación comprueba si el valor numérico de cada defecto
    supera un umbral (40) y genera un mensaje acorde.  Si no se
    suministran `defect_ids` ni `raw_data`, se intenta extraerlos del
    historial.
    """

    defect_ids: List[str] = params.defect_ids or []
    raw_data: List[Dict[str, Any]] = params.raw_data or []

    if (not defect_ids or not raw_data) and params.tool_history:
        hist_ids, hist_data = _derive_inputs_from_history(params.tool_history)
        if not defect_ids:
            defect_ids = hist_ids
        if not raw_data:
            raw_data = hist_data

    if not defect_ids:
        return BusinessRulesOutput(rules=["Sin datos para evaluar reglas de negocio."])

    # Indexamos los datos por defect_id
    data_by_id: Dict[str, Dict[str, Any]] = {row.get("defect_id"): row for row in raw_data}

    rules_results: List[str] = []
    for d in defect_ids:
        row = data_by_id.get(d, {})
        value = row.get("value", 0)
        if value > 40:
            rules_results.append(f"El defecto {d} excede el umbral de valor (valor={value}).")
        else:
            rules_results.append(f"El defecto {d} está dentro de los límites permitidos (valor={value}).")

    return BusinessRulesOutput(rules=rules_results)