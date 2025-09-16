"""MCP Server: Bhinneka (Flights + SearXNG).

Exposes namespaced MCP tools while delegating logic to bhinneka.tools.
"""

from __future__ import annotations

import logging
from fastmcp import FastMCP

from bhinneka.models import ServerStatus
from bhinneka.tools import (
    _find_airports_impl,
    _get_best_flights_impl,
    _get_cheapest_flights_impl,
    _search_flights_impl,
    searx_search_impl,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("bhinneka")


@mcp.tool()
async def flights_search(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    seat_class: str = "economy",
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    max_results: int = 20,
) -> str:
    """Search for flights between two airports."""
    return await _search_flights_impl(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        seat_class=seat_class,
        adults=adults,
        children=children,
        infants_in_seat=infants_in_seat,
        infants_on_lap=infants_on_lap,
        max_results=max_results,
    )


@mcp.tool()
async def flights_find_airports(query: str, limit: int = 10) -> str:
    """Find airports matching a search query."""
    return await _find_airports_impl(query, limit)


@mcp.tool()
async def flights_get_cheapest(
    origin: str,
    destination: str,
    departure_date: str,
    seat_class: str = "economy",
    adults: int = 1,
    max_results: int = 10,
) -> str:
    """Find the cheapest flights for a route, sorted by price."""
    return await _get_cheapest_flights_impl(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        seat_class=seat_class,
        adults=adults,
        max_results=max_results,
    )


@mcp.tool()
async def flights_get_best(
    origin: str,
    destination: str,
    departure_date: str,
    seat_class: str = "economy",
    adults: int = 1,
    max_results: int = 10,
) -> str:
    """Get flights marked as 'best' by Google Flights algorithm."""
    return await _get_best_flights_impl(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        seat_class=seat_class,
        adults=adults,
        max_results=max_results,
    )


# =========================
# SearXNG MCP tools
# =========================


@mcp.tool()
async def searx_web_search(
    query: str,
    engines: str | None = None,
    language: str | None = None,
    time_range: str | None = None,
    safesearch: int = 1,
    max_results: int | None = None,
) -> str:
    """General web search via SearXNG (JSON backend)."""
    return await searx_search_impl(
        query,
        category="general",
        engines=engines,
        language=language or "en",
        time_range=time_range,
        safesearch=safesearch,
        max_results=max_results,
    )


@mcp.tool()
async def searx_images_search(
    query: str,
    engines: str | None = None,
    language: str | None = None,
    safesearch: int = 1,
    max_results: int | None = None,
) -> str:
    """Image search via SearXNG."""
    return await searx_search_impl(
        query,
        category="images",
        engines=engines,
        language=language or "en",
        safesearch=safesearch,
        max_results=max_results,
    )


@mcp.tool()
async def searx_news_search(
    query: str,
    engines: str | None = None,
    language: str | None = None,
    time_range: str | None = None,
    max_results: int | None = None,
) -> str:
    """News search via SearXNG."""
    return await searx_search_impl(
        query,
        category="news",
        engines=engines,
        language=language or "en",
        time_range=time_range,
        safesearch=1,
        max_results=max_results,
    )


@mcp.tool()
async def searx_search_json(
    query: str,
    category: str | None = None,
    engines: str | None = None,
    language: str | None = None,
    time_range: str | None = None,
    safesearch: int = 1,
    max_results: int | None = None,
) -> str:
    """Generic SearXNG search returning compact JSON string."""
    return await searx_search_impl(
        query,
        category=category or "general",
        engines=engines,
        language=language or "en",
        time_range=time_range,
        safesearch=safesearch,
        max_results=max_results,
        return_json=True,
    )


@mcp.tool()
async def get_server_status() -> str:
    """Get current status and capabilities of the MCP server."""
    try:
        status = ServerStatus()
        status_lines = [
            f"🛫 {status.service_name} v{status.version}",
            f"🟢 Status: {status.status.title()}",
            f"📡 Data Source: {status.data_source}",
            "",
            "✅ Capabilities:",
        ]
        for capability in status.capabilities:
            status_lines.append(f"   • {capability.replace('_', ' ').title()}")
        status_lines.extend(["", "📋 Supported Features:"])
        for feature, details in status.supported_features.items():
            status_lines.append(f"   • {feature.replace('_', ' ').title()}: {details}")
        status_lines.extend(
            [
                "",
                "🔧 Usage Examples:",
                "   • flights_search('LAX', 'JFK', '2025-12-25')",
                "   • flights_find_airports('Los Angeles')",
                "   • flights_get_cheapest('SFO', 'LHR', '2025-06-15')",
            ]
        )
        return "\n".join(status_lines)
    except Exception as e:  # noqa: BLE001
        logger.exception("Status check error")
        return f"❌ Error getting server status: {e!s}"


def create_server() -> FastMCP:
    """Create and return the configured FastMCP server instance."""
    return mcp


if __name__ == "__main__":
    # For direct execution (development/testing)
    mcp.run(transport="stdio")
