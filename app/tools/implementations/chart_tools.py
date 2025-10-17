# app/tools/implementations/chart_tools.py (REEMPLAZAR COMPLETO)

import pandas as pd
from pydantic import Field
from typing import List, Dict, Any

from app.tools.core import BaseTool, ToolInput, ToolOutput, register_tool, ToolContext
from app.core.report.charts import ChartBuilder

@register_tool
class ChartGenerationTool(BaseTool):
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
            )