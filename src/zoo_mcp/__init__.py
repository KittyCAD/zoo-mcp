"""Zoo Model Context Protocol (MCP) Server.

A lightweight service that enables AI assistants to execute Zoo commands through the Model Context Protocol (MCP).
"""

import logging
import sys
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("zoo_mcp")
except PackageNotFoundError:
    # package is not installed
    pass

FORMAT = "%(asctime)s | %(levelname)-7s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s"

logging.basicConfig(
    level=logging.INFO, format=FORMAT, handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("zoo_mcp")


class ZooMCPException(Exception):
    """Custom exception for Zoo MCP Server."""

    pass
