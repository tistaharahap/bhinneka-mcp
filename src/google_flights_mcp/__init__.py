"""Google Flights MCP Server - Access flight data via Model Context Protocol."""

from google_flights_mcp.cli import main
from google_flights_mcp.server import create_server

__version__ = "0.1.0"
__all__ = ["create_server", "main"]


def hello() -> str:
    """Legacy hello function."""
    return "Hello from google-flights-mcp!"
