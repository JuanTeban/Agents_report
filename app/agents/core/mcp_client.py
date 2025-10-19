"""Cliente asíncrono para invocar herramientas expuestas por FastMCP."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


class MCPClient:
    """Cliente asíncrono para FastMCP."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 60.0
    ) -> None:
        """Inicializa el cliente MCP."""
        self.base_url = (
            base_url or os.environ.get("FASTMCP_URL", "http://localhost:8000")
        ).rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            follow_redirects=True
        )
        logger.info(f"MCPClient inicializado: {self.base_url}")

    async def get_tools(self) -> List[Dict[str, Any]]:
        """Obtiene el catálogo de tools disponibles."""
        try:
            logger.debug("Obteniendo catálogo desde FastMCP...")
            response = await self._client.get("/tools")
            response.raise_for_status()
            
            data = response.json()
            tools = data.get("tools", [])
            
            logger.info(f"✓ Catálogo: {len(tools)} tools")
            
            return tools
            
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP obteniendo tools: {e}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo tools: {e}")
            raise

    async def invoke(
        self,
        tool_name: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Invoca una tool remota."""
        try:
            logger.debug(f"Invocando '{tool_name}'...")
            
            payload = {"name": tool_name, "args": kwargs}
            response = await self._client.post("/invoke", json=payload)
            response.raise_for_status()
            
            result = response.json().get("result", {})
            success = result.get("success", False)
            
            logger.info(f"{'✓' if success else '✗'} Tool '{tool_name}': {success}")
            
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP invocando '{tool_name}': {e}")
            return {
                "success": False,
                "data": None,
                "error": f"HTTP error: {str(e)}",
                "metadata": {}
            }
        except Exception as e:
            logger.error(f"Error invocando '{tool_name}': {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Error: {str(e)}",
                "metadata": {}
            }

    async def close(self) -> None:
        """Cierra el cliente HTTP."""
        await self._client.aclose()
        logger.debug("MCPClient cerrado")

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Context manager exit."""
        await self.close()