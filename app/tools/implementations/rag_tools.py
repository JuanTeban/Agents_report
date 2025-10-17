# app/tools/implementations/rag_tools.py (REEMPLAZAR COMPLETO)

import re
from pydantic import Field
from typing import List, Dict, Any

from app.tools.core import BaseTool, ToolInput, ToolOutput, register_tool, ToolContext
from app.core.report.retrieval import ReportGeneratorRetriever

@register_tool
class EvidenceRetrievalTool(BaseTool):
    """Recupera evidencia estructurada de defectos."""
    
    class Input(ToolInput):
        # Explícito
        consultant_name: str = Field(
            ...,
            description="Nombre del consultor responsable"
        )
        # Auto-resuelto
        defect_ids: List[str] = Field(
            default_factory=list,
            description="IDs de defectos - se extrae automáticamente de SQL"
        )
    
    @property
    def dependencies(self) -> List[str]:
        return ["sql_data_extraction"]
    
    def resolve_dependencies(self, context: ToolContext) -> Dict[str, Any]:
        """Extrae defect_ids desde SQL result"""
        resolved = {}
        
        sql_result = context.get_successful_result("sql_data_extraction")
        if sql_result and sql_result.data:
            resolved["defect_ids"] = self._extract_defect_ids(sql_result.data)
        else:
            resolved["defect_ids"] = []
        
        return resolved
    
    def _extract_defect_ids(self, sql_data: List[Dict]) -> List[str]:
        """Extrae IDs de defectos de TODAS las filas"""
        ids = set()
        for row in sql_data:
            defect_col = row.get("defectos", "")
            defect_str = str(defect_col)
            match = re.search(r'\b(\d{6,})\b', defect_str)
            if match:
                ids.add(match.group(1))
        return list(ids)
    
    async def _execute_impl(
        self,
        defect_ids: List[str],
        consultant_name: str
    ) -> ToolOutput:
        """Lógica de recuperación de evidencia"""
        try:
            if not defect_ids:
                return ToolOutput(
                    success=False,
                    error="No defect_ids disponibles"
                )
            
            evidence = await self.retriever.get_defect_evidence_structured(
                defect_ids=defect_ids,
                responsable=consultant_name,
                chunks_per_defect=20
            )
            
            # Calculate stats
            total_chunks = 0
            stats_by_defect = {}
            
            for defect_id, sections in evidence.items():
                defect_total = sum(len(chunks) for chunks in sections.values())
                total_chunks += defect_total
                stats_by_defect[defect_id] = {
                    "control": len(sections.get("control", [])),
                    "evidencia": len(sections.get("evidencia", [])),
                    "solucion": len(sections.get("solucion", [])),
                    "total": defect_total
                }
            
            return ToolOutput(
                success=True,
                data=evidence,
                metadata={
                    "total_chunks": total_chunks,
                    "defects_processed": len(defect_ids),
                    "stats_by_defect": stats_by_defect
                }
            )
            
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"Error recuperando evidencia: {str(e)}"
            )