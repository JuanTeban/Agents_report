# app/tools/core/tool_context.py (ARCHIVO NUEVO)

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class ToolResult(BaseModel):
    """Wrapper for tool execution results with metadata"""
    tool_name: str
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()
    
    class Config:
        arbitrary_types_allowed = True

class ToolContext:
    """
    Shared context (blackboard) where tools publish and consume results.
    
    This enables tools to be autonomous - they can retrieve dependencies
    from previous tool executions without the agent's intervention.
    """
    
    def __init__(self):
        self._results: Dict[str, ToolResult] = {}
        self._execution_order: List[str] = []
        
        logger.debug("ToolContext initialized")
    
    def set_result(self, tool_name: str, result: 'ToolOutput') -> None:
        """Publish a tool result to the context"""
        tool_result = ToolResult(
            tool_name=tool_name,
            success=result.success,
            data=result.data,
            error=result.error,
            metadata=result.metadata
        )
        
        self._results[tool_name] = tool_result
        if tool_name not in self._execution_order:
            self._execution_order.append(tool_name)
        
        logger.debug(f"Tool result published: {tool_name} (success={result.success})")
    
    def get_result(self, tool_name: str) -> Optional[ToolResult]:
        """Retrieve a tool result from context"""
        return self._results.get(tool_name)
    
    def has_result(self, tool_name: str) -> bool:
        """Check if a tool has published results"""
        return tool_name in self._results
    
    def get_successful_result(self, tool_name: str) -> Optional[ToolResult]:
        """Get result only if it was successful"""
        result = self.get_result(tool_name)
        return result if result and result.success else None
    
    def get_execution_history(self) -> List[str]:
        """Get list of tools executed in order"""
        return self._execution_order.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize context for logging/debugging"""
        return {
            "execution_order": self._execution_order,
            "results": {
                name: {
                    "success": r.success,
                    "has_data": r.data is not None,
                    "error": r.error,
                    "timestamp": r.timestamp.isoformat()
                }
                for name, r in self._results.items()
            }
        }
    
    def clear(self) -> None:
        """Reset the context (useful for testing)"""
        self._results.clear()
        self._execution_order.clear()