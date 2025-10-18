"""Pydantic schemas for FastMCP tools.

Este módulo agrupa todos los modelos de entrada y salida utilizados por las
herramientas expuestas a través de FastMCP.  Centralizar los modelos en
un único archivo facilita su descubrimiento y mantenimiento.  Las clases
pueden importarse tanto desde los módulos de herramientas como desde
`server.py` al declarar las firmas.
"""

from __future__ import annotations

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ToolCallRecord(BaseModel):
    """Representa un registro histórico de una llamada a herramienta.

    Este modelo captura la información esencial sobre una invocación
    anterior, incluyendo el nombre de la herramienta, los argumentos
    pasados y el resultado devuelto.  Puede ampliarse para incluir
    marcas de tiempo u otros metadatos si se requiere.  El objetivo
    principal de almacenar el historial es permitir a las herramientas
    derivar argumentos faltantes a partir de resultados previos.
    """

    name: str = Field(..., description="Nombre de la tool invocada.")
    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Argumentos que se pasaron a la herramienta."
    )
    result: Dict[str, Any] = Field(
        default_factory=dict,
        description="Resultado devuelto por la herramienta."
    )


# ---------------------------------------------------------------------------
# SQL Data Extraction
# ---------------------------------------------------------------------------

class SQLDataExtractionInput(BaseModel):
    """Modelo de entrada para la herramienta de extracción SQL.

    Esta herramienta espera un nombre de consultor y un tipo de reporte
    para consultar tu almacén de datos o base de datos.  Con base en
    estos parámetros devuelve un conjunto de identificadores de defectos
    y las filas de datos crudos asociadas.
    """

    consultant_name: str = Field(..., description="Nombre completo del consultor.")
    report_type: str = Field(..., description="Tipo de reporte a generar (por ejemplo preview, final).")


class SQLDataExtractionOutput(BaseModel):
    """Modelo de salida para la extracción SQL.

    Contiene la lista de IDs de defecto y las filas de datos crudos
    (representadas como diccionarios).  El campo `raw_data` puede ser
    cualquier estructura serializable que represente las filas de la
    consulta.
    """

    defect_ids: List[str] = Field(..., description="Lista de identificadores de defectos extraídos.")
    raw_data: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Filas crudas devueltas por la consulta SQL."
    )


# ---------------------------------------------------------------------------
# Evidence Retrieval
# ---------------------------------------------------------------------------

class EvidenceRetrievalInput(BaseModel):
    """Modelo de entrada para la recuperación de evidencia.

    Acepta opcionalmente una lista de IDs de defecto y un historial de
    herramientas.  Si `defect_ids` se omite, la herramienta intentará
    extraer los identificadores del historial.  Si se proporcionan ambos,
    `defect_ids` tiene prioridad.
    """

    defect_ids: Optional[List[str]] = Field(
        None,
        description=(
            "Lista de IDs de defecto para recuperar evidencia.  Si se omite, "
            "la herramienta los derivará del `tool_history`."
        ),
    )
    tool_history: Optional[List[ToolCallRecord]] = Field(
        None,
        description=(
            "Registros históricos de herramientas para derivar argumentos "
            "faltantes, como los defect_ids.  Debe contener entradas de "
            "llamadas previas como sql_data_extraction."
        ),
    )


class EvidenceRetrievalOutput(BaseModel):
    """Modelo de salida para la recuperación de evidencia.

    Devuelve una lista de cadenas de evidencia y un campo `notes`
    opcional para contexto adicional o advertencias.  Cada elemento de
    `evidence_list` corresponde a un identificador de defecto.
    """

    evidence_list: List[str] = Field(..., description="Evidencia asociada a cada ID de defecto.")
    notes: Optional[str] = Field(
        None,
        description="Notas o advertencias generadas durante la recuperación de evidencia."
    )


# ---------------------------------------------------------------------------
# Summary Generation
# ---------------------------------------------------------------------------

class SummaryGenerationInput(BaseModel):
    """Modelo de entrada para la generación de resúmenes.

    La herramienta requiere una cadena de consulta y puede recibir
    opcionalmente el historial para derivar evidencia.  La evidencia
    extraída se combinará con la consulta para producir un resumen final.
    """

    query: str = Field(..., description="Pregunta o indicación para generar el resumen.")
    tool_history: Optional[List[ToolCallRecord]] = Field(
        None,
        description="Registros de herramientas para extraer evidencia si se necesita."
    )


class SummaryGenerationOutput(BaseModel):
    """Modelo de salida para la generación de resúmenes.

    Contiene una única cadena con el resumen, la cual representa la
    respuesta agregada a la consulta del usuario, sintetizada a partir
    de la evidencia proporcionada.
    """

    summary: str = Field(..., description="Resumen generado en base a la consulta y la evidencia.")


# ---------------------------------------------------------------------------
# Business Rules
# ---------------------------------------------------------------------------

class BusinessRulesInput(BaseModel):
    """Modelo de entrada para la evaluación de reglas de negocio.

    Acepta una lista de IDs de defecto o datos crudos y evalúa las reglas
    aplicables.  Los defectos pueden provenir de herramientas previas
    (extraídos mediante `tool_history`).
    """

    defect_ids: Optional[List[str]] = Field(
        None,
        description="Lista de IDs de defecto para comprobar contra las reglas."
    )
    raw_data: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Filas de datos crudos que pueden evaluarse mediante las reglas."
    )
    tool_history: Optional[List[ToolCallRecord]] = Field(
        None,
        description="Historial de llamadas para derivar defect_ids o raw_data si faltan."
    )


class BusinessRulesOutput(BaseModel):
    """Modelo de salida para la evaluación de reglas de negocio.

    Devuelve una lista de mensajes que describen qué reglas se han
    disparado o qué resultados se obtuvieron.
    """

    rules: List[str] = Field(..., description="Lista de resultados de las reglas.")


# ---------------------------------------------------------------------------
# Recommendations Generation
# ---------------------------------------------------------------------------

class RecommendationsInput(BaseModel):
    """Modelo de entrada para la generación de recomendaciones.

    Acepta un resumen o lista de evidencias y genera acciones
    recomendadas.  Puede ampliarse para incluir contexto adicional.
    """

    summary: Optional[str] = Field(
        None,
        description="Texto del resumen a partir del cual derivar recomendaciones."
    )
    evidence_list: Optional[List[str]] = Field(
        None,
        description="Lista de evidencias utilizada para sugerir recomendaciones."
    )
    tool_history: Optional[List[ToolCallRecord]] = Field(
        None,
        description="Historial de herramientas para extraer inputs faltantes."
    )


class RecommendationsOutput(BaseModel):
    """Modelo de salida para la generación de recomendaciones.

    Contiene una lista de acciones o próximos pasos sugeridos.
    """

    recommendations: List[str] = Field(..., description="Recomendaciones accionables generadas.")


# ---------------------------------------------------------------------------
# Chart Generation
# ---------------------------------------------------------------------------

class ChartGenerationInput(BaseModel):
    """Modelo de entrada para la generación de gráficas.

    Acepta los datos crudos (como los devueltos por SQL) y un tipo de
    gráfica.  Se pueden añadir opciones adicionales como el título.
    """

    data: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Filas de datos a visualizar en la gráfica."
    )
    chart_type: str = Field(
        ...,
        description="Tipo de gráfica a generar (por ejemplo bar, pie, line)."
    )


class ChartGenerationOutput(BaseModel):
    """Modelo de salida para la generación de gráficas.

    Devuelve una representación de la gráfica generada.  En una
    implementación real podría ser una imagen codificada o un enlace a
    un recurso.  Para simplificar, aquí se devuelve una descripción.
    """

    chart: str = Field(..., description="Representación generada de la gráfica.")
