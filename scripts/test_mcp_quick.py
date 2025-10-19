import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Importar la clase
from app.agents.core.mcp_client import MCPClient

# Verificar que tenga los métodos
print("✓ MCPClient importado correctamente")
print(f"✓ Métodos disponibles: {[m for m in dir(MCPClient) if not m.startswith('_')]}")

# Verificar que get_tools existe
if hasattr(MCPClient, 'get_tools'):
    print("✓ Método get_tools() EXISTE")
else:
    print("✗ ERROR: Método get_tools() NO EXISTE")