<<<<<<< HEAD
# app/tools/implementations/chart_tools.py (REEMPLAZAR COMPLETO)

=======
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
import pandas as pd
from pydantic import Field
from typing import List, Dict, Any

<<<<<<< HEAD
from app.tools.core import BaseTool, ToolInput, ToolOutput, register_tool, ToolContext
=======
from app.tools.core import BaseTool, ToolInput, ToolOutput, register_tool
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
from app.core.report.charts import ChartBuilder

@register_tool
class ChartGenerationTool(BaseTool):
<<<<<<< HEAD
    """Genera gráficos a partir de datos SQL."""
    
    class Input(ToolInput):
        # TODO auto-resuelto (no hay parámetros explícitos)
        sql_data: List[Dict] = Field(
            default_factory=list,
            description="Datos SQL"
        )
    
    @property
    def dependencies(self) -> List[str]:
        return ["sql_data_extraction"]
    
    def resolve_dependencies(self, context: ToolContext) -> Dict[str, Any]:
        """Obtiene sql_data desde contexto"""
        resolved = {}
        
        sql_result = context.get_successful_result("sql_data_extraction")
        if sql_result:
            resolved["sql_data"] = sql_result.data or []
        else:
            resolved["sql_data"] = []
        
        return resolved
    
    async def _execute_impl(self, sql_data: List[Dict]) -> ToolOutput:
=======
    """
    Genera gráficos a partir de datos SQL.
    Reutiliza ChartBuilder existente.
    """
    
    class Input(ToolInput):
        sql_data: List[Dict] = Field(..., description="Datos SQL para visualizar")
    
    @property
    def name(self) -> str:
        return "chart_generation"
    
    @property
    def description(self) -> str:
        return "Genera gráficos (pie, bar) basados en los datos SQL del reporte"
    
    @property
    def input_schema(self) -> type[ToolInput]:
        return self.Input
    
    def __init__(self):
        self.chart_builder = ChartBuilder()
    
    async def execute(self, sql_data: List[Dict]) -> ToolOutput:
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
        try:
            if not sql_data:
                return ToolOutput(
                    success=False,
                    data={},
                    error="No hay datos para generar gráficos"
                )
            
            df = pd.DataFrame(sql_data)
            charts = {}
            
            # Configuración de gráficos
            chart_configs = [
                ("estado_distribution", "estado_de_defecto", "pie"),
                ("module_distribution", "modulo", "bar"),
                ("blocker_status", "bloqueante_escenarios", "pie"),
                ("age_by_defect", "antiguedad_del_defecto_promedio_en_dias", "bar")
            ]
            
            for chart_name, column, chart_type in chart_configs:
                if column in df.columns:
                    chart = self.chart_builder.build_chart(df, column, chart_type)
                    if chart:
                        charts[chart_name] = chart
            
            return ToolOutput(
                success=True,
                data=charts,
                metadata={
                    "total_charts": len(charts),
                    "chart_names": list(charts.keys())
                }
            )
            
        except Exception as e:
            return ToolOutput(
                success=False,
                data={},
                error=f"Error generando gráficos: {str(e)}"
<<<<<<< HEAD
            )
=======
            )
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
