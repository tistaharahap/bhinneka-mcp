"""CLI interface for Google Flights MCP Server using Typer."""

from __future__ import annotations

import os
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel

from google_flights_mcp.server import create_server

# Initialize Typer app and Rich console
app = typer.Typer(
    name="google-flights-mcp",
    help="🛫 Google Flights MCP Server - Access flight data via Model Context Protocol",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


@app.command("serve")
def serve_command(
    host: Annotated[str, typer.Option("--host", "-h", help="Host to bind the server to")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", "-p", help="Port to bind the server to")] = 8000,
    transport: Annotated[str, typer.Option("--transport", "-t", help="Transport protocol: 'stdio' or 'http'")] = "stdio",
    log_level: Annotated[str, typer.Option("--log-level", "-l", help="Logging level")] = "INFO",
) -> None:
    """
    🚀 Start the Google Flights MCP server.

    By default uses stdio transport for Claude Desktop and MCP clients.
    Use --transport http for remote HTTP access.
    """
    try:
        # Set log level
        import logging

        logging.getLogger().setLevel(getattr(logging, log_level.upper()))

        # Create and configure server
        mcp = create_server()

        # Handle transport types
        if transport.lower() == "stdio":
            # stdio transport for Claude Desktop
            startup_panel = Panel.fit(
                f"[bold green]🛫 Google Flights MCP Server[/bold green]\n\n"
                f"[cyan]Transport:[/cyan] stdio\n"
                f"[cyan]Log Level:[/cyan] {log_level}\n\n"
                f"[yellow]Ready for Claude Desktop and MCP clients[/yellow]\n"
                f"[dim]Press Ctrl+C to stop[/dim]",
                title="MCP Server Starting",
                border_style="green",
            )
            rprint(startup_panel)

            # Start in stdio mode
            mcp.run(transport="stdio")

        elif transport.lower() == "http":
            # HTTP transport for remote access
            actual_transport = "streamable-http"
            startup_panel = Panel.fit(
                f"[bold green]🛫 Google Flights MCP Server[/bold green]\n\n"
                f"[cyan]Transport:[/cyan] {actual_transport}\n"
                f"[cyan]Host:[/cyan] {host}\n"
                f"[cyan]Port:[/cyan] {port}\n"
                f"[cyan]Log Level:[/cyan] {log_level}\n\n"
                f"[yellow]Server URL:[/yellow] http://{host}:{port}/mcp\n"
                f"[dim]Press Ctrl+C to stop[/dim]",
                title="HTTP Server Starting",
                border_style="green",
            )
            rprint(startup_panel)

            # Start the HTTP server
            mcp.run(
                transport=actual_transport,
                host=host,
                port=port,
                log_level=log_level.lower(),
            )
        else:
            rprint(f"[red]❌ Invalid transport: {transport}. Use 'stdio' or 'http'[/red]")
            raise typer.Exit(1)

    except KeyboardInterrupt:
        rprint("\n[yellow]👋 Server stopped gracefully[/yellow]")
    except Exception as e:
        rprint(f"[red]❌ Error starting server: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("dev")
def dev_command(
    log_level: Annotated[str, typer.Option("--log-level", "-l", help="Logging level")] = "DEBUG",
) -> None:
    """
    🔧 Start the server in development mode.

    Uses stdio transport for local development and testing.
    Suitable for use with MCP Inspector and direct integration.
    """
    try:
        import logging

        logging.getLogger().setLevel(getattr(logging, log_level.upper()))

        # Create server
        mcp = create_server()

        dev_panel = Panel.fit(
            f"[bold blue]🔧 Development Mode[/bold blue]\n\n"
            f"[cyan]Transport:[/cyan] stdio\n"
            f"[cyan]Log Level:[/cyan] {log_level}\n\n"
            f"[yellow]Use with MCP Inspector or direct stdio connection[/yellow]\n"
            f"[dim]Press Ctrl+C to stop[/dim]",
            title="Development Server",
            border_style="blue",
        )
        rprint(dev_panel)

        # Start in stdio mode
        mcp.run(transport="stdio")

    except KeyboardInterrupt:
        rprint("\n[yellow]👋 Development server stopped[/yellow]")
    except Exception as e:
        rprint(f"[red]❌ Error starting development server: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("status")
def status_command() -> None:
    """
    📊 Check server status and capabilities.

    Displays information about the MCP server's capabilities,
    supported features, and current configuration.
    """
    try:
        from google_flights_mcp.models import ServerStatus

        status = ServerStatus()

        status_info = (
            f"[bold green]{status.service_name} v{status.version}[/bold green]\n\n"
            f"[cyan]Status:[/cyan] {status.status.title()}\n"
            f"[cyan]Data Source:[/cyan] {status.data_source}\n\n"
            f"[bold]✅ Capabilities:[/bold]\n"
        )

        for capability in status.capabilities:
            status_info += f"  • {capability.replace('_', ' ').title()}\n"

        status_info += "\n[bold]📋 Supported Features:[/bold]\n"
        for feature, details in status.supported_features.items():
            status_info += f"  • [cyan]{feature.replace('_', ' ').title()}:[/cyan] {details}\n"

        status_panel = Panel.fit(
            status_info,
            title="Server Status",
            border_style="green",
        )
        rprint(status_panel)

    except Exception as e:
        rprint(f"[red]❌ Error getting status: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("test-search")
def test_search_command(
    origin: Annotated[str, typer.Argument(help="Origin airport code (e.g., LAX)")],
    destination: Annotated[str, typer.Argument(help="Destination airport code (e.g., JFK)")],
    departure_date: Annotated[str, typer.Argument(help="Departure date (YYYY-MM-DD)")],
    seat_class: Annotated[str, typer.Option("--class", "-c", help="Seat class")] = "economy",
    adults: Annotated[int, typer.Option("--adults", "-a", help="Number of adults")] = 1,
    max_results: Annotated[int, typer.Option("--max", "-m", help="Maximum results")] = 5,
) -> None:
    """
    🔍 Test flight search functionality.

    Performs a direct flight search to test the server's capabilities
    without requiring a full MCP client setup.
    """
    try:
        import asyncio

        from google_flights_mcp.server import _search_flights_impl

        async def run_search() -> str:
            return await _search_flights_impl(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                seat_class=seat_class,
                adults=adults,
                max_results=max_results,
            )

        rprint("\n[bold blue]🔍 Testing flight search...[/bold blue]")
        rprint(f"[dim]Route: {origin.upper()} → {destination.upper()} on {departure_date}[/dim]\n")

        # Run the search
        result = asyncio.run(run_search())

        # Display results in a panel
        result_panel = Panel.fit(
            result,
            title="Flight Search Results",
            border_style="blue",
        )
        rprint(result_panel)

    except Exception as e:
        rprint(f"[red]❌ Error testing search: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("test-airports")
def test_airports_command(
    query: Annotated[str, typer.Argument(help="Airport search query")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="Maximum results")] = 5,
) -> None:
    """
    🏢 Test airport search functionality.

    Searches for airports matching the query to test the
    airport lookup capabilities.
    """
    try:
        import asyncio

        from google_flights_mcp.server import _find_airports_impl

        async def run_search() -> str:
            return await _find_airports_impl(query=query, limit=limit)

        rprint("\n[bold blue]🏢 Testing airport search...[/bold blue]")
        rprint(f"[dim]Query: '{query}'[/dim]\n")

        # Run the search
        result = asyncio.run(run_search())

        # Display results in a panel
        result_panel = Panel.fit(
            result,
            title="Airport Search Results",
            border_style="blue",
        )
        rprint(result_panel)

    except Exception as e:
        rprint(f"[red]❌ Error testing airport search: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("version")
def version_command() -> None:
    """📋 Show version information."""
    try:
        from google_flights_mcp.models import ServerStatus

        status = ServerStatus()
        rprint(f"[bold green]{status.service_name}[/bold green] version [cyan]{status.version}[/cyan]")

    except Exception as e:
        rprint(f"[red]❌ Error getting version: {e}[/red]")
        raise typer.Exit(1) from e


def main() -> None:
    """Main CLI entry point."""
    # Set environment variable for rich output
    os.environ.setdefault("FORCE_COLOR", "1")

    try:
        app()
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    main()
