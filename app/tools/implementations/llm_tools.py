<<<<<<< HEAD
# app/tools/implementations/llm_tools.py (REEMPLAZAR COMPLETO)

from pydantic import Field
from typing import List, Dict, Any

from app.tools.core import BaseTool, ToolInput, ToolOutput, register_tool, ToolContext
from app.core.ia.llm import get_llm_provider
from app.core.report.prompts import ReportGeneratorPromptManager
from app.core.report.retrieval import ReportGeneratorRetriever

=======
from pydantic import Field
from typing import List, Dict, Any

from app.tools.core import BaseTool, ToolInput, ToolOutput, register_tool
from app.core.ia.llm import get_llm_provider
from app.core.report.prompts import ReportGeneratorPromptManager
from app.core.report.retrieval import ReportGeneratorRetriever
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
@register_tool
class BusinessRulesTool(BaseTool):
    """
    Recupera reglas de negocio relevantes.
<<<<<<< HEAD
=======
    Reutiliza RAGRetriever.get_business_rules()
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
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
<<<<<<< HEAD
        return "Recupera reglas de negocio relevantes desde ChromaDB"
=======
        return "Recupera reglas de negocio relevantes desde ChromaDB usando búsqueda semántica"
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
    
    @property
    def input_schema(self) -> type[ToolInput]:
        return self.Input
    
<<<<<<< HEAD
    @property
    def dependencies(self) -> List[str]:
        return []
    
    def __init__(self):
        self.retriever = ReportGeneratorRetriever()
    
    async def _execute_impl(self, query: str, top_k: int = 5) -> ToolOutput:
=======
    def __init__(self):
        self.retriever = ReportGeneratorRetriever()
    
    async def execute(self, query: str, top_k: int = 5) -> ToolOutput:
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
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
<<<<<<< HEAD
=======
                data=None,
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
                error=f"Error recuperando business rules: {str(e)}"
            )


@register_tool
<<<<<<< HEAD
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
=======
class TextGenerationTool(BaseTool):
    """
    Genera texto usando LLM con un prompt específico.
    Tool genérica para cualquier generación de texto.
    """
    
    class Input(ToolInput):
        prompt: str = Field(..., description="Prompt completo para el LLM")
        temperature: float = Field(default=0.7, description="Temperatura (0-1)")
        max_tokens: int = Field(default=2048, description="Tokens máximos")
    
    @property
    def name(self) -> str:
        return "text_generation"
    
    @property
    def description(self) -> str:
        return "Genera texto usando el LLM configurado con un prompt personalizado"
    
    @property
    def input_schema(self) -> type[ToolInput]:
        return self.Input
    
    def __init__(self):
        self.llm = get_llm_provider()
    
    async def execute(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> ToolOutput:
        try:
            response = await self.llm.generate_async(
                prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return ToolOutput(
                success=True,
                data=response.content,
                metadata={
                    "model": response.model,
                    "usage": response.usage or {}
                }
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                data=None,
                error=f"Error generando texto: {str(e)}"
            )


@register_tool
class SummaryGenerationTool(BaseTool):
    """
    Genera resumen ejecutivo del reporte.
    Usa PromptManager para construir el prompt.
    """
    
    class Input(ToolInput):
        consultant_name: str = Field(..., description="Nombre del consultor")
        sql_data: List[Dict] = Field(..., description="Datos SQL extraídos")
        rag_context: Dict = Field(..., description="Contexto RAG recuperado")
    
    @property
    def name(self) -> str:
        return "summary_generation"
    
    @property
    def description(self) -> str:
        return "Genera resumen ejecutivo del reporte basado en datos SQL y contexto RAG"
    
    @property
    def input_schema(self) -> type[ToolInput]:
        return self.Input
    
    def __init__(self):
        self.llm = get_llm_provider()
        self.prompt_manager = ReportGeneratorPromptManager()
    
    async def execute(
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
        self,
        consultant_name: str,
        sql_data: List[Dict],
        rag_context: Dict
    ) -> ToolOutput:
<<<<<<< HEAD
        """Lógica de generación de resumen"""
=======
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
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
<<<<<<< HEAD
=======
                data=None,
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
                error=f"Error generando resumen: {str(e)}"
            )


@register_tool
class RecommendationsGenerationTool(BaseTool):
    """
    Genera recomendaciones técnicas.
<<<<<<< HEAD
    
    **Autonomía**: Obtiene sql_data y rag_context desde resultados previos.
=======
    Usa PromptManager para construir el prompt.
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
    """
    
    class Input(ToolInput):
        consultant_name: str = Field(..., description="Nombre del consultor")
<<<<<<< HEAD
        # Estos se auto-resuelven:
        sql_data: List[Dict] = Field(default_factory=list)
        rag_context: Dict = Field(default_factory=dict)
=======
        sql_data: List[Dict] = Field(..., description="Datos SQL extraídos")
        rag_context: Dict = Field(..., description="Contexto RAG recuperado")
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
    
    @property
    def name(self) -> str:
        return "recommendations_generation"
    
    @property
    def description(self) -> str:
<<<<<<< HEAD
        return "Genera recomendaciones técnicas basadas en diagnóstico"
=======
        return "Genera recomendaciones técnicas basadas en diagnóstico de defectos"
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
    
    @property
    def input_schema(self) -> type[ToolInput]:
        return self.Input
    
<<<<<<< HEAD
    @property
    def dependencies(self) -> List[str]:
        return ["sql_data_extraction", "evidence_retrieval", "business_rules"]
    
=======
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
    def __init__(self):
        self.llm = get_llm_provider()
        self.prompt_manager = ReportGeneratorPromptManager()
    
<<<<<<< HEAD
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
=======
    async def execute(
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
        self,
        consultant_name: str,
        sql_data: List[Dict],
        rag_context: Dict
    ) -> ToolOutput:
<<<<<<< HEAD
        """Lógica de generación de recomendaciones"""
=======
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
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
<<<<<<< HEAD
=======
                data=None,
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
                error=f"Error generando recomendaciones: {str(e)}"
            )