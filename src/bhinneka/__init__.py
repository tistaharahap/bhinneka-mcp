"""Bhinneka MCP Toolkit: Flights + Web Search."""

from bhinneka.cli import main
from bhinneka.server import create_server

__version__ = "0.1.0"
__all__ = ["create_server", "main"]


def hello() -> str:
    """Legacy hello function."""
    return "Hello from bhinneka!"

