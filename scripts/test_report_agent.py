"""Tests para ReportAgent con FastMCP."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.agents.report.agent import ReportAgent
from app.agents.core.mcp_client import MCPClient


@pytest.fixture
def mock_mcp_client():
    """Mock del cliente MCP."""
    client = AsyncMock(spec=MCPClient)
    
    # Mock get_tools
    client.get_tools.return_value = [
        {
            "name": "sql_data_extraction",
            "description": "Extrae datos SQL",
            "input_schema": {
                "type": "object",
                "properties": {
                    "consultant_name": {"type": "string", "description": "Nombre del consultor"}
                },
                "required": ["consultant_name"]
            }
        },
        {
            "name": "evidence_retrieval",
            "description": "Recupera evidencia",
            "input_schema": {
                "type": "object",
                "properties": {
                    "defect_ids": {"type": "array", "description": "IDs de defectos"},
                    "consultant_name": {"type": "string", "description": "Consultor"}
                },
                "required": ["defect_ids", "consultant_name"]
            }
        },
        {
            "name": "summary_generation",
            "description": "Genera resumen",
            "input_schema": {
                "type": "object",
                "properties": {
                    "consultant_name": {"type": "string"},
                    "sql_data": {"type": "array"},
                    "rag_context": {"type": "object"}
                },
                "required": ["consultant_name", "sql_data", "rag_context"]
            }
        }
    ]
    
    # Mock invoke para diferentes tools
    def mock_invoke(tool_name, **kwargs):
        if tool_name == "sql_data_extraction":
            return {
                "success": True,
                "data": [
                    {"defectos": "8000001234", "modulo": "RE", "estado": "Abierto"}
                ],
                "metadata": {"row_count": 1}
            }
        elif tool_name == "evidence_retrieval":
            return {
                "success": True,
                "data": {
                    "8000001234": {
                        "evidencia": [{"content": "Evidence text"}]
                    }
                },
                "metadata": {"total_chunks": 1}
            }
        elif tool_name == "summary_generation":
            return {
                "success": True,
                "data": "Resumen ejecutivo generado",
                "metadata": {}
            }
        else:
            return {"success": False, "error": "Unknown tool"}
    
    client.invoke = AsyncMock(side_effect=mock_invoke)
    client.base_url = "http://localhost:8000"
    
    return client


@pytest.fixture
def mock_llm():
    """Mock del LLM provider."""
    llm = Mock()
    
    # Simular respuestas del LLM
    responses = [
        # Primera iteración: usar sql_data_extraction
        Mock(
            content='{"reasoning": "Need SQL data", "action": "use_tool", "tool_name": "sql_data_extraction", "tool_args": {"consultant_name": "Test"}}',
            usage={"tokens": 100}
        ),
        # Segunda iteración: usar evidence_retrieval
        Mock(
            content='{"reasoning": "Need evidence", "action": "use_tool", "tool_name": "evidence_retrieval", "tool_args": {}}',
            usage={"tokens": 100}
        ),
        # Tercera iteración: generar resumen
        Mock(
            content='{"reasoning": "Generate summary", "action": "use_tool", "tool_name": "summary_generation", "tool_args": {}}',
            usage={"tokens": 100}
        ),
        # Cuarta iteración: respuesta final
        Mock(
            content='{"reasoning": "Done", "action": "final_answer", "answer": "Report generated"}',
            usage={"tokens": 100}
        ),
    ]
    
    llm.generate_async = AsyncMock(side_effect=responses)
    
    return llm


@pytest.mark.asyncio
async def test_report_agent_initialization(mock_mcp_client):
    """Test: ReportAgent se inicializa correctamente con MCP client."""
    agent = ReportAgent(mcp_client=mock_mcp_client)
    
    assert agent.name == "ReportAgent"
    assert agent.mcp_client == mock_mcp_client
    assert agent.max_iterations == 15


@pytest.mark.asyncio
async def test_report_agent_loads_tools_catalog(mock_mcp_client):
    """Test: ReportAgent carga el catálogo de tools desde FastMCP."""
    agent = ReportAgent(mcp_client=mock_mcp_client)
    
    # Cargar catálogo
    await agent._load_tools_catalog()
    
    assert len(agent._tools_catalog) == 3
    tool_names = [t["name"] for t in agent._tools_catalog]
    assert "sql_data_extraction" in tool_names
    assert "evidence_retrieval" in tool_names
    assert "summary_generation" in tool_names


@pytest.mark.asyncio
async def test_report_agent_generate_report(mock_mcp_client, mock_llm):
    """Test: ReportAgent genera un reporte completo."""
    agent = ReportAgent(mcp_client=mock_mcp_client)
    agent.llm = mock_llm
    
    report = await agent.generate_report(
        consultant_name="Test Consultant",
        report_type="preview"
    )
    
    # Verificar estructura del reporte
    assert report["consultant"] == "Test Consultant"
    assert report["type"] == "preview"
    assert "generated_at" in report
    assert "data" in report
    assert "sections" in report
    assert "metadata" in report
    
    # Verificar metadata
    assert report["metadata"]["version"] == "3.0-fastmcp"
    assert report["metadata"]["agent"] == "ReportAgent"
    assert report["metadata"]["mcp_url"] == "http://localhost:8000"
    
    # Verificar que se invocaron las tools
    assert mock_mcp_client.invoke.call_count >= 3


@pytest.mark.asyncio
async def test_report_agent_handles_missing_consultant():
    """Test: ReportAgent maneja error cuando falta consultant_name."""
    agent = ReportAgent(mcp_client=AsyncMock())
    
    report = await agent.generate_report(consultant_name="")
    
    assert report["type"] == "error"
    assert "Error" in report["sections"]["summary"]


@pytest.mark.asyncio
async def test_report_agent_extract_defect_ids():
    """Test: ReportAgent extrae correctamente IDs de defectos."""
    agent = ReportAgent(mcp_client=AsyncMock())
    
    sql_data = [
        {"defectos": "8000001234"},
        {"defectos": "8000005678"},
        {"defectos": "invalid"}
    ]
    
    ids = agent._extract_defect_ids(sql_data)
    
    assert len(ids) == 2
    assert "8000001234" in ids
    assert "8000005678" in ids


@pytest.mark.asyncio
async def test_mcp_client_get_tools():
    """Test: MCPClient obtiene catálogo de tools."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [
                {"name": "test_tool", "description": "Test"}
            ]
        }
        mock_client.return_value.get = AsyncMock(return_value=mock_response)
        
        client = MCPClient(base_url="http://test:8000")
        tools = await client.get_tools()
        
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"


@pytest.mark.asyncio
async def test_mcp_client_invoke():
    """Test: MCPClient invoca tools correctamente."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {
                "success": True,
                "data": "test_data"
            }
        }
        mock_client.return_value.post = AsyncMock(return_value=mock_response)
        
        client = MCPClient(base_url="http://test:8000")
        result = await client.invoke("test_tool", arg1="value1")
        
        assert result["success"] is True
        assert result["data"] == "test_data"