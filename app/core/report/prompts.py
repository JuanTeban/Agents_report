import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from app.shared.prompts.base_prompt_manager import BasePromptManager

logger = logging.getLogger(__name__)

class ReportGeneratorPromptManager(BasePromptManager):
    """
    Gestiona la construcción de prompts específicos para el generador de reportes.
    """
    def __init__(self):
        prompts_path = Path(__file__).parent / "prompts.json"
        super().__init__(prompts_path=prompts_path)

    def get_sql_prompt(self, consultant_name: str, schema_context: List[Dict]) -> str:
        """Construye el prompt para la generación de SQL."""
        template = self._get_template("sql_generation_for_report_prompt")
        context_str = "\n".join([doc.get("content", "") for doc in schema_context])
        
        formatted_prompt = template.replace(":RESPONSABLE", consultant_name)
        
        return formatted_prompt.format(
            question=f"Datos del consultor {consultant_name}",
            context=context_str
        )

    def get_summary_prompt(self, consultant_name: str, sql_data: List[Dict], rag_context: Dict) -> str:
        """Construye el prompt para el resumen ejecutivo."""
        template = self._get_template("report_summary_prompt")
        

        business_rules = "\n".join([r.get("content", "") for r in rag_context.get("business_rules", [])])
        
        defect_ids_from_sql = set()
        for row in sql_data:
            defect = str(row.get("defectos", ""))
            import re
            match = re.search(r'\b(\d{6,})\b', defect)
            if match:
                defect_ids_from_sql.add(match.group(1))
        
        control_evidence_by_defect = {}
        evidence_by_defect = rag_context.get("evidence_by_defect", {})
        
        for defect_id in defect_ids_from_sql:
            sections = evidence_by_defect.get(defect_id, {})
            control_chunks = sections.get("control", [])
            
            if control_chunks:
                control_text = "\n\n".join([chunk.get("content", "") for chunk in control_chunks])
                control_evidence_by_defect[defect_id] = control_text
            else:
                control_evidence_by_defect[defect_id] = (
                    "No se encontró información de control para este defecto en la base de datos. "
                    "Usar únicamente los datos del SQL para el contexto."
                )
        
        if control_evidence_by_defect:
            table_evidence_text = "\n\n".join([
                f"### DEFECTO {defect_id}\n{text}"
                for defect_id, text in control_evidence_by_defect.items()
            ])
        else:
            table_evidence_text = "No se encontró evidencia de control en la base de datos para ningún defecto."
        
        data_json = json.dumps(sql_data, indent=2, ensure_ascii=False)
        
        return template.format(
            consultant_name=consultant_name,
            data_json=data_json,
            snippets_text=business_rules,
            table_evidence_text=table_evidence_text
        )

    def get_recommendations_prompt(self, consultant_name: str, sql_data: List[Dict], rag_context: Dict) -> str:
        """Construye el prompt para las recomendaciones."""
        template = self._get_template("report_recommendations_prompt")
        
        business_rules = "\n".join([r.get("content", "") for r in rag_context.get("business_rules", [])])
        
        defect_ids_from_sql = set()
        for row in sql_data:
            defect = str(row.get("defectos", ""))
            import re
            match = re.search(r'\b(\d{6,})\b', defect)
            if match:
                defect_ids_from_sql.add(match.group(1))

        multimodal_evidence_by_defect = {}
        evidence_by_defect = rag_context.get("evidence_by_defect", {})
        
        for defect_id in defect_ids_from_sql:
            sections = evidence_by_defect.get(defect_id, {})
            evidencia_chunks = sections.get("evidencia", [])
            
            if evidencia_chunks:
                evidence_texts = []
                for chunk in evidencia_chunks[:10]:
                    content = chunk.get("content", "")
                    preview = content[:500] + "..." if len(content) > 500 else content
                    evidence_texts.append(preview)
                multimodal_evidence_by_defect[defect_id] = "\n\n".join(evidence_texts)
            else:
                multimodal_evidence_by_defect[defect_id] = (
                    "No se encontró evidencia multimodal detallada para este defecto en la base de datos. "
                    "Basar el análisis únicamente en los datos estructurados del SQL."
                )
        
        if multimodal_evidence_by_defect:
            multimodal_evidence_text = "\n\n".join([
                f"### DEFECTO {defect_id}\n{text}"
                for defect_id, text in multimodal_evidence_by_defect.items()
            ])
        else:
            multimodal_evidence_text = "No se encontró evidencia detallada en la base de datos para ningún defecto."
        
        historical_solutions = "No se encontraron soluciones históricas relevantes."
        
        data_json = json.dumps(sql_data, indent=2, ensure_ascii=False)
        
        return template.format(
            consultant_name=consultant_name,
            data_json=data_json,
            snippets_text=business_rules,
            multimodal_evidence=multimodal_evidence_text,
            historical_solutions_text=historical_solutions
        )