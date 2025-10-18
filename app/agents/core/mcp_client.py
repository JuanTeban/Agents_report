from __future__ import annotations

import os
from typing import Any, Dict, List
import httpx


class MCPClient:
    """Cliente asíncrono para invocar herramientas expuestas por FastMCP."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = (base_url or os.environ.get("FASTMCP_URL", "http://localhost:8000")).rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def get_tools(self) -> List[Dict[str, Any]]:
        response = await self._client.get("/tools")
        response.raise_for_status()
        return response.json().get("tools", [])

    async def invoke(self, tool_name: str, **kwargs: Any) -> Any:
        payload = {"name": tool_name, "args": kwargs}
        response = await self._client.post("/invoke", json=payload)
        response.raise_for_status()
        return response.json().get("result")

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "MCPClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()