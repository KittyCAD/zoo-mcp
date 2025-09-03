from zoo_mcp.server import mcp

if __name__ == "__main__":
    try:
        mcp.run()

    except KeyboardInterrupt:
        print("Shutting down MCP server...")
        exit(0)
