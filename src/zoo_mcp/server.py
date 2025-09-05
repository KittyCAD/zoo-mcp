from mcp.server.fastmcp import FastMCP

from zoo_mcp import logger
from zoo_mcp.tools import text_to_cad

mcp = FastMCP(
    name="Zoo MCP Server",
)


@mcp.tool()
async def call_text_to_cad(prompt: str) -> str:
    """Generate CAD code from a text prompt.

    Args:
        prompt (str): The text prompt to be converted to CAD code.

    Returns:
        str: The generated CAD code if Text-to-CAD is successful, otherwise the error message.
    """
    logger.info(f"Received Text To CAD prompt: {prompt}")
    return await text_to_cad(prompt=prompt)


if __name__ == "__main__":
    mcp.run()
