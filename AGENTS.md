## Development Commands

### Environment Setup
- `uv venv` - Create virtual environment
- `uv pip install -e .` - Install package in development mode
- `export ZOO_API_TOKEN="your_api_key_here"` - Set required Zoo API token

### Running the Server
- `uv run -m zoo_mcp` - Start the MCP server locally
- `uv run mcp run src/zoo_mcp/server.py` - Alternative method using mcp package
- `uv run mcp dev src/zoo_mcp/server.py` - Run server with MCP Inspector for testing

### Testing and Quality
- `uv run -n auto pytest` - Run all tests
- `uv run pytest tests/test_server.py` - Run specific test file
- `ruff check` - Run linter
- `ruff format` - Format code
- `uv run ty check` - Type check source code

### Integration Commands
- `uv run mcp install src/zoo_mcp/server.py` - Install server for Claude Desktop integration

## Architecture

This is a Model Context Protocol (MCP) server that exposes Zoo's AI-powered CAD generation tools to AI assistants. The architecture consists of:

### Core Components
- `src/zoo_mcp/server.py` - FastMCP server that defines the MCP interface and exposes the `call_text_to_cad` tool
- `src/zoo_mcp/tools.py` - Contains the `text_to_cad` function that interfaces with Zoo's KittyCAD API
- `src/zoo_mcp/__init__.py` - Package initialization with logging configuration

### Key Dependencies
- `kittycad` - Official Zoo API client for accessing Text-to-CAD functionality
- `mcp[cli]` - Model Context Protocol framework for AI assistant integration
- `pytest-asyncio` - For testing async functions

### API Integration
The server connects to Zoo's Text-to-CAD API using the KittyCAD client. All requests require a valid `ZOO_API_TOKEN` environment variable. The `text_to_cad` function handles:
- Sending prompts to Zoo's ML endpoint
- Polling for completion status
- Returning either generated KCL code (on success) or error messages (on failure)

### Testing Strategy  
Tests are located in `tests/test_server.py` and cover:
- Basic tool functionality
- Success scenarios (valid CAD prompts)
- Failure scenarios (invalid prompts)
- All tests are async and use pytest-asyncio

## Package Structure
Built as a standard Python package using setuptools with source code in `src/zoo_mcp/`. The package can be installed via pip/uv or used directly as a module.