import logging
from typing import List, Dict, Any, Optional
from app.shared.retrieval.base_retriever import BaseRetriever

logger = logging.getLogger(__name__)

class ReportGeneratorRetriever(BaseRetriever):
    async def get_schema_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return await self.query_collection(
            collection_key="schema_knowledge",
            query=query,
            top_k=top_k
        )

    async def get_business_rules(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return await self.query_collection(
            collection_key="business_rules",
            query=query,
            top_k=top_k
        )

    async def get_defect_chunks_by_section(
        self,
        defect_id: str,
        section_title_norm: str,
        responsable: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        where_clauses = [
            {"defect_id_digits": {"$eq": defect_id}},
            {"section_title_norm": {"$eq": section_title_norm}}
        ]
        
        if responsable:
            responsable_norm = self._normalize_text(responsable)
            where_clauses.append({"responsable_norm": {"$eq": responsable_norm}})
        
        where_filter = {"$and": where_clauses} if len(where_clauses) > 1 else where_clauses[0]
        
        logger.info(f"Filtrando chunks para defecto {defect_id}, sección {section_title_norm}")
        return await self.filter_collection(
            collection_key="multimodal_evidence",
            where_filter=where_filter,
            limit=limit
        )

    async def get_defect_evidence_structured(
        self,
        defect_ids: List[str],
        responsable: Optional[str] = None,
        chunks_per_defect: int = 50
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        structured_evidence = {}
        sections_map = {
            "control": "control_de_la_plantilla_y_documento",
            "evidencia": "descripcion_y_evidencia_hallazgo",
            "solucion": "respuesta_consultoria"
        }
        
        for defect_id in defect_ids:
            structured_evidence[defect_id] = {}
            for key, section_norm in sections_map.items():
                chunks = await self.get_defect_chunks_by_section(
                    defect_id=defect_id,
                    section_title_norm=section_norm,
                    responsable=responsable,
                    limit=chunks_per_defect
                )
                structured_evidence[defect_id][key] = chunks
            
            logger.info(
                f"Defecto {defect_id}: {len(structured_evidence[defect_id]['control'])} control, "
                f"{len(structured_evidence[defect_id]['evidencia'])} evidencia, "
                f"{len(structured_evidence[defect_id]['solucion'])} solución"
            )
        
        return structured_evidence