"""Implementación de la herramienta de extracción SQL.

Esta función simula la extracción de IDs de defecto y datos crudos de
una base de datos.  Acepta el nombre del consultor y el tipo de
reporte y devuelve una lista de defectos y datos ficticios.
"""

from __future__ import annotations

from typing import List, Dict, Any

from ..schemas import SQLDataExtractionInput, SQLDataExtractionOutput


async def sql_data_extraction(params: SQLDataExtractionInput) -> SQLDataExtractionOutput:
    """Extraer datos de una base según el consultor y el tipo de reporte.

    Esta implementación de ejemplo crea identificadores de defecto
    basándose en el nombre del consultor y en el tipo de reporte, y
    devuelve filas de datos ficticios.  En producción deberías
    reemplazar esto por consultas contra tu almacén de datos.

    Args:
        params: Instancia de `SQLDataExtractionInput` con `consultant_name`
            y `report_type`.

    Returns:
        `SQLDataExtractionOutput` con IDs de defecto y datos crudos.
    """

    # Derivamos IDs sencillos de las primeras letras del nombre y del tipo
    base = params.consultant_name.split()[0].upper()[:3]  # primeras 3 letras
    report_suffix = params.report_type.lower()[0]          # primera letra del tipo

    defect_ids: List[str] = [f"{base}-{report_suffix}{i}" for i in range(1, 4)]

    # Creamos datos crudos de ejemplo por cada defecto
    raw_data: List[Dict[str, Any]] = []
    for d in defect_ids:
        raw_data.append(
            {
                "defect_id": d,
                "consultant": params.consultant_name,
                "report_type": params.report_type,
                "description": f"Descripción ficticia del defecto {d}",
                # Campo numérico ficticio para reglas de negocio
                "value": len(d) * 10,
            }
        )

    return SQLDataExtractionOutput(defect_ids=defect_ids, raw_data=raw_data)