# app/mcp/mcp_proxy.py
from typing import Any, Dict, Type
from fastmcp import Client
from app.tools.core.base_tool import BaseTool, ToolInput, ToolOutput
from app.config.settings import MCP_SERVER_URL

class MCPProxyTool(BaseTool):
    """
    Proxy que envuelve una herramienta remota MCP y la expone como BaseTool.
    Usa fastmcp.Client para llamar al servidor remoto.
    """
    def __init__(self, name: str, description: str, input_schema: Type[ToolInput]):
        self._name = name
        self._description = description
        self._input_schema = input_schema

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def input_schema(self) -> Type[ToolInput]:
        return self._input_schema

    async def execute(self, **kwargs) -> ToolOutput:
        async with Client(MCP_SERVER_URL) as client:
            remote_result: Dict[str, Any] = await client.call_tool(self._name, kwargs)
        # Convierte el resultado en ToolOutput (espera campos success, data, error, metadata)
        return ToolOutput(**remote_result)