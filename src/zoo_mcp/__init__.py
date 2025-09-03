"""Zoo Model Context Protocol (MCP) Server.

A lightweight service that enables AI assistants to execute Zoo commands through the Model Context Protocol (MCP).
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("zoo_mcp")
except PackageNotFoundError:
    # package is not installed
    pass