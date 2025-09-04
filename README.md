# Zoo Model Context Protocol (MCP) Server
An MCP server housing various Zoo built utilities

## Installation
1. [Ensure uv has been installed](https://docs.astral.sh/uv/getting-started/installation/)

2. [Create a uv environment](https://docs.astral.sh/uv/pip/environments/)
    ```bash
    uv venv
    ```

3. [Activate your uv environment (Optional)](https://docs.astral.sh/uv/pip/environments/#using-a-virtual-environment)

4. Install the package from GitHub
    ```bash
    uv pip install git+ssh://git@github.com/KittyCAD/zoo-mcp.git
    ```

## Running the Server

The server can be started locally by using uv
`uv run -m zoo_mcp`

## Integrations

The server can be used as is by [running the server](#running-the-server) or importing directly into your python code.
```python
from zoo_mcp.server import mcp

mcp.run()
```

Individual tools can be used in your own python code as well
```python
from mcp.server.fastmcp import FastMCP
from zoo_mcp.tools import text_to_cad

mcp = FastMCP(name="My Example Server")

@mcp.tool()
async def my_text_text_to_cad(prompt: str) -> str:
    """
    Example tool that uses the text_to_cad function from zoo_mcp.tools
    """
    return await text_to_cad(prompt=prompt)
```

The server can be integrated with [Claude desktop](https://claude.ai/download) using the following command
```bash 
  uv run mcp install src/zoo_mcp/server.py
```

The server can also be tested using the [MCP Inspector](https://modelcontextprotocol.io/legacy/tools/inspector#python)
```bash
  uv run mcp dev src/zoo_mcp/server.py
```