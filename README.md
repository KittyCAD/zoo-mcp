# Zoo Model Context Protocol (MCP) Server

An MCP server housing various Zoo built utilities

## Prerequisites

1. An API key for Zoo, get one [here](https://zoo.dev/account)
2. An environment variable `ZOO_API_TOKEN` set to your API key
    ```bash
    export ZOO_API_TOKEN="your_api_key_here"
    ```

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

The server can be started locally by using uv and the zoo_mcp module
```bash
uv run -m zoo_mcp
```

The server can also be run with the [mcp package](https://github.com/modelcontextprotocol/python-sdk)
```bash
  uv run mcp run src/zoo_mcp/server.py
```

## Integrations

The server can be used as is by [running the server](#running-the-server) or importing directly into your python code.
```python
from zoo_mcp.server import mcp

mcp.run()
```

Individual tools can be used in your own python code as well

```python
from mcp.server.fastmcp import FastMCP
from zoo_mcp.tools import _text_to_cad

mcp = FastMCP(name="My Example Server")


@mcp.tool()
async def my_text_text_to_cad(prompt: str) -> str:
    """
    Example tool that uses the text_to_cad function from zoo_mcp.tools
    """
    return await _text_to_cad(prompt=prompt)
```

The server can be integrated with [Claude desktop](https://claude.ai/download) using the following command
```bash 
  uv run mcp install src/zoo_mcp/server.py
```

The server can also be tested using the [MCP Inspector](https://modelcontextprotocol.io/legacy/tools/inspector#python)
```bash
  uv run mcp dev src/zoo_mcp/server.py
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on the [GitHub repository](https://github.com/KittyCAD/zoo-mcp)

PRs will need to pass tests and linting before being merged.

### [ruff](https://docs.astral.sh/ruff/) is used for linting and formatting.
```bash
  uvx ruff check
  uvx ruff format
```

### [ty](https://docs.astral.sh/ty/) is used for type checking.
```bash
  uvx ty check src/
```

## Testing

The server includes tests located in [`tests`](`tests`). To run the tests, use the following command:
```bash
  uv run pytest
```