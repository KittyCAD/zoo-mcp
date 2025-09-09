import sys

from zoo_mcp import logger
from zoo_mcp.server import mcp

if __name__ == "__main__":
    try:
        logger.info("Starting MCP server...")
        mcp.run(transport="stdio")

    except KeyboardInterrupt:
        logger.info("Shutting down MCP server...")
    except Exception as e:
        logger.exception("Server encountered an error: %s", e)
        sys.exit(1)
