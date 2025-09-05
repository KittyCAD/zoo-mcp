from mcp.server.fastmcp import FastMCP

from zoo_mcp import logger
from zoo_mcp.tools import _text_to_cad

mcp = FastMCP(
    name="Zoo MCP Server",
)


@mcp.tool()
async def text_to_cad(prompt: str) -> str:
    """Generate a CAD model as KCL code from a text prompt.

    Args:
        prompt (str): The text prompt to be realized as KCL code.

    Returns:
        str: The generated KCL code if Text-to-CAD is successful, otherwise the error message.
    """
    logger.info(f"Received Text-To-CAD prompt: {prompt}")
    return await _text_to_cad(prompt=prompt)


if __name__ == "__main__":
    mcp.run()
