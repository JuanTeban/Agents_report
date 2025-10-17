<<<<<<< HEAD
# app/tools/core/base_tool.py (REEMPLAZAR COMPLETO)

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

# Import forward reference
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .tool_context import ToolContext

=======
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
class ToolInput(BaseModel):
    """Schema base de entrada para tools"""
    pass

class ToolOutput(BaseModel):
    """Schema estandarizado de salida"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True

class BaseTool(ABC):
    """
    Clase base abstracta para todas las tools del sistema.
    
<<<<<<< HEAD
    **Patrón de Dependency Injection:**
    Las tools modernas son autónomas y resuelven sus propias dependencias.
=======
    Cada tool debe:
    - Definir un nombre único
    - Proveer descripción clara
    - Especificar schema de entrada (Pydantic)
    - Implementar método execute async
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre único de la tool"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción para LLM function calling"""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> type[ToolInput]:
        """Schema Pydantic de entrada"""
        pass
    
<<<<<<< HEAD
    @property
    def dependencies(self) -> List[str]:
        """
        Lista de tools de las que esta tool depende.
        Override este método para declarar dependencias explícitas.
        """
        return []
    
    def resolve_dependencies(
        self, 
        context: 'ToolContext'
    ) -> Dict[str, Any]:
        """
        Resuelve parámetros auto-resueltos desde el contexto.
        
        IMPORTANTE: Este método NO recibe kwargs del LLM.
        Solo tiene acceso al ToolContext y debe retornar
        un dict con los parámetros auto-resueltos.
        
        Por defecto retorna dict vacío.
        Override para implementar lógica de resolución.
        """
        return {}
    
    @abstractmethod
    async def _execute_impl(self, **kwargs) -> ToolOutput:
        """
        Implementación real de la tool.
        Recibe argumentos ya resueltos y validados.
        """
        pass
    
    async def execute(
        self, 
        context: 'ToolContext', 
        **kwargs
    ) -> ToolOutput:
        """
        Ejecuta la tool con separación automática de parámetros.
        
        Flow:
        1. Separar parámetros explícitos vs auto-resueltos
        2. Resolver dependencias (ignora lo que el LLM haya pasado para parámetros auto-resueltos)
        3. Merge y validar
        4. Ejecutar
        """
        try:
            # 🆕 Step 1: Clasificar parámetros según schema
            explicit_params, auto_resolved_params = self._classify_parameters()
            
            # 🆕 Step 2: Extraer SOLO parámetros explícitos de kwargs
            explicit_kwargs = {
                k: v for k, v in kwargs.items() 
                if k in explicit_params
            }
            
            # 🆕 Step 3: Resolver dependencias (esto SIEMPRE se ejecuta)
            # Pasamos un dict vacío para parámetros auto-resueltos
            auto_resolved_kwargs = self.resolve_dependencies(context)
            
            # 🆕 Step 4: Merge (explícitos + auto-resueltos)
            final_kwargs = {**auto_resolved_kwargs, **explicit_kwargs}
            
            # Step 5: Validar
            validated = self.input_schema(**final_kwargs)
            
            # Step 6: Ejecutar
            result = await self._execute_impl(**validated.model_dump())
            
            return result
            
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"Error en {self.name}: {str(e)}"
            )

    def _classify_parameters(self) -> tuple[set[str], set[str]]:
        """
        Clasifica parámetros del schema en explícitos vs auto-resueltos.
        
        Returns:
            (explicit_params, auto_resolved_params)
        """
        schema = self.input_schema.model_json_schema()
        properties = schema.get('properties', {})
        required = set(schema.get('required', []))
        
        explicit_params = set()
        auto_resolved_params = set()
        
        for param_name, param_info in properties.items():
            # Si es requerido, es explícito
            if param_name in required:
                explicit_params.add(param_name)
            # Si tiene default, es auto-resuelto
            elif 'default' in param_info:
                auto_resolved_params.add(param_name)
            else:
                # Opcional sin default -> explícito
                explicit_params.add(param_name)
        
        return explicit_params, auto_resolved_params
    
    def to_llm_schema(self) -> Dict[str, Any]:
        """Genera schema JSON compatible con LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema.model_json_schema(),
            "dependencies": self.dependencies
        }
=======
    @abstractmethod
    async def execute(self, **kwargs) -> ToolOutput:
        """
        Ejecuta la tool con los parámetros validados.
        
        Los kwargs serán validados automáticamente contra input_schema
        antes de llegar aquí.
        """
        pass
    
    def to_llm_schema(self) -> Dict[str, Any]:
        """
        Genera schema JSON compatible con LLM function calling.
        
        Returns:
            {
                "name": "tool_name",
                "description": "...",
                "parameters": {...}  # JSON Schema
            }
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema.model_json_schema()
        }
    
    def validate_and_execute(self, **kwargs) -> ToolOutput:
        """
        Valida entrada y ejecuta (wrapper para validación).
        En v2 esto será async, por ahora wrapper sync.
        """
        try:
            # Validar con Pydantic
            validated = self.input_schema(**kwargs)
            # Ejecutar (nota: en producción esto debe ser await)
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Si ya hay loop, retornar future
                raise RuntimeError("Use execute() directamente en contexto async")
            return loop.run_until_complete(self.execute(**validated.model_dump()))
        except Exception as e:
            return ToolOutput(success=False, error=str(e))
>>>>>>> 407859c2224dea0a0b7e7954953fa17accdb3491
