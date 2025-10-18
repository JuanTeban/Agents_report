"""Implementación de la herramienta de generación de gráficas.

Acepta datos crudos y un tipo de gráfica y devuelve una descripción
ficticia de la gráfica generada.  En una implementación real
utilizarías una biblioteca de gráficos y devolverías una imagen o
enlace.
"""

from __future__ import annotations

from typing import List, Dict, Any

from ..schemas import ChartGenerationInput, ChartGenerationOutput


async def chart_generation(params: ChartGenerationInput) -> ChartGenerationOutput:
    """Generar una descripción de gráfica a partir de datos.

    Args:
        params: `ChartGenerationInput` con los datos y el tipo de gráfica.

    Returns:
        `ChartGenerationOutput` con una descripción de la gráfica generada.
    """

    num_points = len(params.data)
    chart_desc = (
        f"Se ha generado un gráfico de tipo '{params.chart_type}' con {num_points} registros."
    )
    if params.data:
        first_row = params.data[0]
        chart_desc += f" La primera fila de datos: {first_row}."

    return ChartGenerationOutput(chart=chart_desc)
