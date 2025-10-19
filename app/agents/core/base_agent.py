"""Clase base para agentes con soporte para tools remotas vía FastMCP."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

from app.utils.logger import get_flow_logger
from app.config.settings_agents import BASE_AGENT_INSTRUCTIONS
from .agent_message import AgentMessage
from .mcp_client import MCPClient


class ToolOutput:
    """Wrapper para outputs de tools (compatibilidad con código existente)."""
    
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None, metadata: Optional[Dict] = None):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
    
    def model_dump(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }


class BaseAgent(ABC):
    """Agente base con razonamiento y uso de tools remotas vía FastMCP.
    
    Implementa:
    - Loop de razonamiento (Thought → Action → Observation)
    - Invocación de tools remotas mediante MCPClient
    - Logging detallado
    - Memoria de conversación
    """
    
    def __init__(
        self,
        name: str,
        mcp_client: Optional[MCPClient] = None,
        llm_provider: Optional[Any] = None,
        max_iterations: int = 10,
        response_format_instructions: Optional[str] = None
    ):
        """Inicializa el agente.
        
        Args:
            name: Nombre del agente
            mcp_client: Cliente MCP para tools remotas. Si None, se crea uno nuevo.
            llm_provider: Proveedor de LLM. Si None, se obtiene el por defecto.
            max_iterations: Número máximo de iteraciones del loop de razonamiento
            response_format_instructions: Instrucciones de formato para el LLM
        """
        self.name = name
        self.mcp_client = mcp_client
        self.llm = llm_provider or self._get_default_llm()
        self.max_iterations = max_iterations
        self.response_format_instructions = response_format_instructions or ""
        
        self.logger = get_flow_logger(
            flow_name=f"agent_{name}",
            sub_dir="logs_agents",
            log_level=logging.DEBUG,
            enable_console=True
        )
        
        self.memory: List[AgentMessage] = []
        self._current_run_context: Dict[str, Any] = {}
        self._tools_catalog: List[Dict[str, Any]] = []
        
        self.logger.log_info(f"Agent '{name}' initialized")
    
    def _get_default_llm(self):
        """Obtiene proveedor LLM configurado"""
        from app.core.ia.llm import get_llm_provider
        return get_llm_provider()
    
    @abstractmethod
    async def process_task(self, task: str, context: Dict[str, Any]) -> AgentMessage:
        """Método principal que cada agente debe implementar.
        
        Args:
            task: Descripción de la tarea a realizar
            context: Contexto adicional necesario
        
        Returns:
            AgentMessage con el resultado
        """
        pass
    
    async def _load_tools_catalog(self) -> None:
        """Carga el catálogo de tools desde el servidor FastMCP."""
        if not self.mcp_client:
            self.logger.log_warning("No MCP client configured, tools catalog will be empty")
            self._tools_catalog = []
            return
        
        try:
            self.logger.log_info("Loading tools catalog from FastMCP server...")
            self._tools_catalog = await self.mcp_client.get_tools()
            tool_names = [t.get("name") for t in self._tools_catalog]
            self.logger.log_info(f"Tools catalog loaded: {len(self._tools_catalog)} tools")
            self.logger.log_data("tools_catalog", {"tools": tool_names})
        except Exception as e:
            self.logger.log_error(e, "Failed to load tools catalog")
            self._tools_catalog = []
    
    async def run(self, task: str, context: Optional[Dict] = None) -> AgentMessage:
        """Ejecuta el agente con loop de razonamiento.
        
        Args:
            task: Tarea a realizar
            context: Contexto opcional
            
        Returns:
            AgentMessage con el resultado final
        """
        self.logger.start_flow({
            "agent": self.name,
            "task": task,
            "context": context
        })
        
        context = context or {}
        iteration = 0
        
        self._current_run_context = context
        
        # Cargar catálogo de tools al inicio
        await self._load_tools_catalog()
        
        try:
            async with self.logger.step(
                "agent_reasoning",
                f"Agent {self.name} reasoning loop"
            ):
                while iteration < self.max_iterations:
                    iteration += 1
                    self.logger.log_info(f"Iteration {iteration}/{self.max_iterations}")
                    
                    thought = await self._think(task, context)
                    self.logger.log_data(
                        "thought",
                        thought,
                        f"Agent decision (iteration {iteration})"
                    )
                    
                    if thought.get("action") == "final_answer":
                        self.logger.log_info("Agent reached final answer")
                        result = AgentMessage(
                            sender=self.name,
                            content=thought.get("answer", ""),
                            metadata={
                                "iterations": iteration,
                                "context": context,
                                "reasoning": thought.get("reasoning", "")
                            },
                            success=True
                        )
                        self.memory.append(result)
                        
                        self._current_run_context = {}
                        
                        self.logger.end_flow(success=True)
                        return result
                    
                    if thought.get("action") == "use_tool":
                        tool_name = thought.get("tool_name")
                        tool_args = thought.get("tool_args", {})
                        
                        observation = await self._execute_tool(tool_name, tool_args)
                        self.logger.log_data(
                            "observation",
                            observation.model_dump(),
                            f"Tool result: {tool_name}"
                        )
                        
                        context["last_observation"] = observation.model_dump()
                        context["tool_history"] = context.get("tool_history", [])
                        context["tool_history"].append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result": observation.model_dump()
                        })
                        
                        self._current_run_context = context
                
                self.logger.log_warning(f"Max iterations ({self.max_iterations}) reached")
                error_result = AgentMessage(
                    sender=self.name,
                    content="No pude completar la tarea en el límite de iteraciones",
                    metadata={
                        "error": "max_iterations",
                        "iterations": iteration,
                        "context": context
                    },
                    success=False
                )
                
                self._current_run_context = {}
                
                self.logger.end_flow(success=False, error="Max iterations")
                return error_result
                
        except Exception as e:
            self.logger.log_error(e, "Error in agent execution")
            error_result = AgentMessage(
                sender=self.name,
                content=f"Error durante ejecución: {str(e)}",
                metadata={"error": str(e), "context": context},
                success=False
            )
            
            self._current_run_context = {}
            
            self.logger.end_flow(success=False, error=str(e))
            return error_result
    
    async def _think(self, task: str, context: Dict) -> Dict[str, Any]:
        """Razonamiento: LLM decide basándose en instrucciones y catálogo de tools.
        
        Returns:
            {
                "reasoning": "...",
                "action": "use_tool" | "final_answer",
                "tool_name": "...",
                "tool_args": {...},
                "answer": "..."
            }
        """
        full_prompt = self._build_full_prompt(task, context)
        
        self.logger.log_llm_request(
            full_prompt,
            type(self.llm).__name__,
            {"temperature": 0.3, "task": "reasoning"}
        )
        
        response = await self.llm.generate_async(full_prompt, temperature=0.3)
        
        self.logger.log_llm_response(
            response.content,
            type(self.llm).__name__,
            response.usage or {}
        )
        
        try:
            decision = self._parse_llm_decision(response.content)
            return decision
        except Exception as e:
            self.logger.log_warning(f"Error parseando decisión LLM: {e}")
            return self._fallback_decision(response.content, context)

    def _build_full_prompt(self, task: str, context: Dict) -> str:
        """Construye prompt completo para el LLM."""
        
        agent_instructions = getattr(self, 'agent_instructions', '')
        
        tools_catalog = self._get_tools_catalog()
        
        tool_history = context.get("tool_history", [])
        history_text = self._format_history_for_llm(tool_history)
        
        last_obs = context.get("last_observation")
        observation_text = self._format_last_observation(last_obs)
        
        analysis_guide = self._get_analysis_guide(tool_history, task)
        
        return f"""
{BASE_AGENT_INSTRUCTIONS}

{agent_instructions}

## TOOLS DISPONIBLES (FastMCP):
{tools_catalog}

## TU TAREA ACTUAL:
{task}

## CONTEXTO:
- Consultor: {context.get('consultant_name', 'N/A')}
- Tipo: {context.get('report_type', 'N/A')}

## HISTORIAL DE TOOLS EJECUTADAS:
{history_text}

## ÚLTIMA OBSERVACIÓN:
{observation_text}

{analysis_guide}
   
## FORMATO DE RESPUESTA:  
{self.response_format_instructions}
"""

    def _get_tools_catalog(self) -> str:
        """Genera catálogo de tools desde FastMCP."""
        if not self._tools_catalog:
            return "No hay tools disponibles (FastMCP no configurado o vacío)"
        
        catalog = []
        for tool in self._tools_catalog:
            name = tool.get("name", "unknown")
            description = tool.get("description", "Sin descripción")
            input_schema = tool.get("input_schema", {})
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            param_desc = []
            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "any")
                param_description = param_info.get("description", "sin descripción")
                req_marker = " (requerido)" if param_name in required else " (opcional)"
                param_desc.append(
                    f"  - {param_name} ({param_type}){req_marker}: {param_description}"
                )
            
            params_text = "\n".join(param_desc) if param_desc else "  - Sin parámetros"
            
            catalog.append(
                f"**{name}**\n"
                f"  Descripción: {description}\n"
                f"  Parámetros:\n{params_text}"
            )
        
        return "\n\n".join(catalog)

    def _format_history_for_llm(self, tool_history: List[Dict]) -> str:
        """Formatea historial de herramientas para el LLM."""
        if not tool_history:
            return "Sin historial (es la primera iteración)"
        
        formatted = []
        for i, entry in enumerate(tool_history, 1):
            tool_name = entry.get("tool")
            args = entry.get("args", {})
            result = entry.get("result", {})
            success = result.get("success")
            status = "✓ ÉXITO" if success else "✗ FALLÓ"
            
            if success:
                data = result.get("data")
                metadata = result.get("metadata", {})
                
                # Formato específico por tool
                if tool_name == "sql_data_extraction":
                    row_count = metadata.get("row_count", 0)
                    formatted.append(
                        f"{i}. {status} - Tool: {tool_name}\n"
                        f"   Args: {args}\n"
                        f"   RESULTADOS: {row_count} filas extraídas"
                    )
                elif tool_name == "evidence_retrieval":
                    total_chunks = metadata.get("total_chunks", 0)
                    formatted.append(
                        f"{i}. {status} - Tool: {tool_name}\n"
                        f"   RESULTADOS: {total_chunks} chunks de evidencia"
                    )
                else:
                    data_preview = str(data)[:200] if data else "Sin datos"
                    formatted.append(
                        f"{i}. {status} - Tool: {tool_name}\n"
                        f"   Data preview: {data_preview}..."
                    )
            else:
                error = result.get("error", "Error desconocido")
                formatted.append(
                    f"{i}. {status} - Tool: {tool_name}\n"
                    f"   Error: {error}"
                )
        
        return "\n\n".join(formatted)

    def _format_last_observation(self, last_obs: Any) -> str:
        """Formatea última observación."""
        if not last_obs:
            return "Sin observaciones previas (primera iteración)"
        
        if isinstance(last_obs, dict):
            success = last_obs.get("success")
            if success:
                return "✓ Última tool exitosa"
            else:
                error = last_obs.get("error", "Error desconocido")
                return f"✗ Última tool falló: {error}"
        
        return "Observación disponible"

    def _get_analysis_guide(self, tool_history: List[Dict], task: str) -> str:
        """Genera guía de análisis."""
        completed_tools = {entry["tool"] for entry in tool_history}
        
        return f"""
## ANÁLISIS PASO A PASO:

1. **REVISAR HISTORIAL:**
   - Tools ejecutadas: {', '.join(completed_tools) if completed_tools else 'ninguna'}
   - Total de acciones: {len(tool_history)}

2. **EVALUAR PROGRESO:**
   - ¿He cumplido el objetivo de la tarea?
   - ¿Qué información tengo disponible?
   - ¿Qué me falta para completar?

3. **DECIDIR SIGUIENTE ACCIÓN:**
   - Si tengo todo lo necesario → final_answer
   - Si falta información → use_tool (decidir cuál)
   - Si algo falló → evaluar si puedo continuar
"""

    def _parse_llm_decision(self, llm_response: str) -> Dict[str, Any]:
        """Parsea respuesta JSON del LLM."""
        import json
        import re
        
        cleaned = re.sub(r'```json\s*', '', llm_response)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        cleaned = cleaned.strip()
        
        decision = json.loads(cleaned)
        
        if "action" not in decision:
            raise ValueError("Falta campo 'action' en decisión")
        
        if decision["action"] == "use_tool":
            if "tool_name" not in decision:
                raise ValueError("action=use_tool pero falta 'tool_name'")
            # Verificar que la tool existe en el catálogo
            tool_names = [t.get("name") for t in self._tools_catalog]
            if decision["tool_name"] not in tool_names:
                available = ', '.join(tool_names)
                raise ValueError(
                    f"Tool '{decision['tool_name']}' no existe en catálogo FastMCP. "
                    f"Disponibles: {available}"
                )
            if "tool_args" not in decision:
                decision["tool_args"] = {}
        
        elif decision["action"] == "final_answer":
            if "answer" not in decision:
                raise ValueError("action=final_answer pero falta 'answer'")
        
        return decision

    def _fallback_decision(self, llm_response: str, context: Dict) -> Dict[str, Any]:
        """Decisión de emergencia si falla el parsing."""
        self.logger.log_warning("Usando fallback decision")
        
        tool_names = [t.get("name") for t in self._tools_catalog]
        for tool_name in tool_names:
            if tool_name in llm_response.lower():
                return {
                    "reasoning": "Fallback: detecté mención de tool",
                    "action": "use_tool",
                    "tool_name": tool_name,
                    "tool_args": {}
                }
        
        return {
            "reasoning": "Fallback: no pude parsear decisión",
            "action": "final_answer",
            "answer": llm_response[:500]
        }
    
    async def _execute_tool(self, tool_name: str, tool_args: Dict) -> ToolOutput:
        """Ejecuta tool mediante MCPClient.
        
        Args:
            tool_name: Nombre de la tool
            tool_args: Argumentos para la tool
            
        Returns:
            ToolOutput con el resultado
        """
        if not self.mcp_client:
            self.logger.log_error(
                Exception("No MCP client configured"),
                "Cannot execute tool without MCP client"
            )
            return ToolOutput(
                success=False,
                data=None,
                error="No MCP client configured"
            )
        
        # Verificar que la tool existe
        tool_names = [t.get("name") for t in self._tools_catalog]
        if tool_name not in tool_names:
            available = ', '.join(tool_names)
            self.logger.log_warning(
                f"Tool '{tool_name}' no encontrada. Disponibles: {available}"
            )
            return ToolOutput(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' no disponible. Disponibles: {available}"
            )
        
        self.logger.log_info(f"Executing tool via FastMCP: {tool_name}", tool_args)
        
        try:
            # Invocar vía MCP
            result = await self.mcp_client.invoke(tool_name, **tool_args)
            
            # Convertir a ToolOutput
            output = ToolOutput(
                success=result.get("success", False),
                data=result.get("data"),
                error=result.get("error"),
                metadata=result.get("metadata", {})
            )
            
            status = "✓ success" if output.success else "✗ failed"
            self.logger.log_info(f"Tool {tool_name} {status}")
            
            return output
            
        except Exception as e:
            self.logger.log_error(e, f"Tool {tool_name} execution failed")
            return ToolOutput(
                success=False,
                data=None,
                error=f"Error ejecutando tool vía FastMCP: {str(e)}"
            )