# app/tools/implementations/llm_tools.py (REEMPLAZAR COMPLETO)

from pydantic import Field
from typing import List, Dict, Any

from app.tools.core import BaseTool, ToolInput, ToolOutput, register_tool, ToolContext
from app.core.ia.llm import get_llm_provider
from app.core.report.prompts import ReportGeneratorPromptManager
from app.core.report.retrieval import ReportGeneratorRetriever

@register_tool
class BusinessRulesTool(BaseTool):
    """
    Recupera reglas de negocio relevantes.
    """
    
    class Input(ToolInput):
        query: str = Field(
            ...,
            description="Query de búsqueda (módulos, categorías, etc.)"
        )
        top_k: int = Field(
            default=5,
            description="Número de reglas a recuperar"
        )
    
    @property
    def name(self) -> str:
        return "business_rules"
    
    @property
    def description(self) -> str:
        return "Recupera reglas de negocio relevantes desde ChromaDB"
    
    @property
    def input_schema(self) -> type[ToolInput]:
        return self.Input
    
    @property
    def dependencies(self) -> List[str]:
        return []
    
    def __init__(self):
        self.retriever = ReportGeneratorRetriever()
    
    async def _execute_impl(self, query: str, top_k: int = 5) -> ToolOutput:
        try:
            rules = await self.retriever.get_business_rules(query, top_k)
            
            return ToolOutput(
                success=True,
                data=rules,
                metadata={
                    "count": len(rules),
                    "query": query
                }
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"Error recuperando business rules: {str(e)}"
            )


@register_tool
class SummaryGenerationTool(BaseTool):
    """Genera resumen ejecutivo del reporte."""
    
    class Input(ToolInput):
        # Explícito (required)
        consultant_name: str = Field(
            ..., 
            description="Nombre del consultor"
        )
        
        # Auto-resueltos (tienen default)
        sql_data: List[Dict] = Field(
            default_factory=list,
            description="Datos SQL - se obtiene automáticamente"
        )
        rag_context: Dict = Field(
            default_factory=dict,
            description="Contexto RAG - se obtiene automáticamente"
        )
    
    @property
    def dependencies(self) -> List[str]:
        return ["sql_data_extraction", "evidence_retrieval", "business_rules"]
    
    def resolve_dependencies(self, context: ToolContext) -> Dict[str, Any]:
        """
        Resuelve SIEMPRE desde el contexto.
        No recibe kwargs del LLM, así que no hay confusión.
        """
        resolved = {}
        
        # SQL Data
        sql_result = context.get_successful_result("sql_data_extraction")
        if sql_result:
            resolved["sql_data"] = sql_result.data or []
        else:
            resolved["sql_data"] = []
        
        # RAG Context
        evidence_result = context.get_successful_result("evidence_retrieval")
        rules_result = context.get_successful_result("business_rules")
        
        resolved["rag_context"] = {
            "evidence_by_defect": (
                evidence_result.data if evidence_result else {}
            ),
            "business_rules": (
                rules_result.data if rules_result else []
            ),
            "schemas": []
        }
        
        return resolved
    
    async def _execute_impl(
        self,
        consultant_name: str,
        sql_data: List[Dict],
        rag_context: Dict
    ) -> ToolOutput:
        """Lógica de generación de resumen"""
        try:
            prompt = self.prompt_manager.get_summary_prompt(
                consultant_name,
                sql_data,
                rag_context
            )
            
            response = await self.llm.generate_async(prompt)
            
            return ToolOutput(
                success=True,
                data=response.content,
                metadata={
                    "model": response.model,
                    "usage": response.usage or {},
                    "section": "summary"
                }
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"Error generando resumen: {str(e)}"
            )


@register_tool
class RecommendationsGenerationTool(BaseTool):
    """
    Genera recomendaciones técnicas.
    
    **Autonomía**: Obtiene sql_data y rag_context desde resultados previos.
    """
    
    class Input(ToolInput):
        consultant_name: str = Field(..., description="Nombre del consultor")
        # Estos se auto-resuelven:
        sql_data: List[Dict] = Field(default_factory=list)
        rag_context: Dict = Field(default_factory=dict)
    
    @property
    def name(self) -> str:
        return "recommendations_generation"
    
    @property
    def description(self) -> str:
        return "Genera recomendaciones técnicas basadas en diagnóstico"
    
    @property
    def input_schema(self) -> type[ToolInput]:
        return self.Input
    
    @property
    def dependencies(self) -> List[str]:
        return ["sql_data_extraction", "evidence_retrieval", "business_rules"]
    
    def __init__(self):
        self.llm = get_llm_provider()
        self.prompt_manager = ReportGeneratorPromptManager()
    
    def resolve_dependencies(
        self, 
        context: ToolContext, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extrae sql_data, evidencia y reglas desde contexto.
        """
        # SQL Data
        sql_result = context.get_successful_result("sql_data_extraction")
        if sql_result:
            kwargs["sql_data"] = sql_result.data or []
        
        # RAG Context
        evidence_result = context.get_successful_result("evidence_retrieval")
        rules_result = context.get_successful_result("business_rules")
        
        kwargs["rag_context"] = {
            "evidence_by_defect": (
                evidence_result.data if evidence_result and evidence_result.data else {}
            ),
            "business_rules": (
                rules_result.data if rules_result and rules_result.data else []
            ),
            "schemas": []
        }
        
        return kwargs
    
    async def _execute_impl(
        self,
        consultant_name: str,
        sql_data: List[Dict],
        rag_context: Dict
    ) -> ToolOutput:
        """Lógica de generación de recomendaciones"""
        try:
            prompt = self.prompt_manager.get_recommendations_prompt(
                consultant_name,
                sql_data,
                rag_context
            )
            
            response = await self.llm.generate_async(prompt)
            
            return ToolOutput(
                success=True,
                data=response.content,
                metadata={
                    "model": response.model,
                    "usage": response.usage or {},
                    "section": "recommendations"
                }
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"Error generando recomendaciones: {str(e)}"
            )