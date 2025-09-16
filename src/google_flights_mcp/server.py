"""Google Flights MCP Server implementation."""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from fast_flights import FlightData, Passengers, get_flights, search_airport
from fastmcp import FastMCP
from pydantic import ValidationError

from google_flights_mcp.airport_data import search_airports_local
from google_flights_mcp.models import (
    Airport,
    AirportSearchRequest,
    AirportSearchResponse,
    FlightDetails,
    FlightSearchRequest,
    FlightSearchResponse,
    ServerStatus,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("google-flights")


def _safe_int_conversion(value: Any, default: int = 0) -> int:
    """Safely convert a value to integer, handling strings and None."""
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert '{value}' to integer, using default {default}")
            return default
    return default


def _safe_bool_conversion(value: Any, default: bool = False) -> bool:
    """Safely convert a value to boolean, handling strings and None."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    if isinstance(value, int):
        return bool(value)
    return default


def _parse_flight_data(flight_dict: dict[str, Any]) -> FlightDetails:
    """Parse raw flight data from fast-flights into our model."""
    return FlightDetails(
        airline=flight_dict.get("name", "Unknown Airline"),
        flight_number=flight_dict.get("flight_number"),
        departure_time=flight_dict.get("departure", ""),
        arrival_time=flight_dict.get("arrival", ""),
        departure_airport=flight_dict.get("departure_airport", ""),
        arrival_airport=flight_dict.get("arrival_airport", ""),
        duration=flight_dict.get("duration", ""),
        stops=_safe_int_conversion(flight_dict.get("stops"), 0),
        price=flight_dict.get("price", "N/A"),
        is_best=_safe_bool_conversion(flight_dict.get("is_best"), False),
        departure_terminal=flight_dict.get("departure_terminal"),
        arrival_terminal=flight_dict.get("arrival_terminal"),
    )


def _format_flight_summary(flight: FlightDetails) -> str:
    """Format flight information for human-readable display."""
    stops_text = "non-stop" if flight.stops == 0 else f"{flight.stops} stop{'s' if flight.stops > 1 else ''}"
    best_indicator = " ⭐" if flight.is_best else ""

    summary = [
        f"{flight.airline}{best_indicator}",
        f"  🛫 Departure: {flight.departure_time}",
        f"  🛬 Arrival: {flight.arrival_time}",
        f"  ⏱️  Duration: {flight.duration} ({stops_text})",
        f"  💰 Price: {flight.price}",
    ]

    if flight.flight_number:
        summary.insert(1, f"  ✈️  Flight: {flight.flight_number}")

    return "\n".join(summary)


async def _search_flights_impl(
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
    """
    Search for flights between two airports.

    Args:
        origin: Origin airport IATA code (e.g., 'LAX', 'JFK')
        destination: Destination airport IATA code (e.g., 'NRT', 'LHR')
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date for round trips (YYYY-MM-DD format)
        seat_class: Seat class (economy, premium-economy, business, first)
        adults: Number of adult passengers (1-9)
        children: Number of child passengers (0-8)
        infants_in_seat: Number of infants with seats (0-5)
        infants_on_lap: Number of infants on lap (0-5)
        max_results: Maximum number of flights to return (1-100)

    Returns:
        Formatted flight search results as a string
    """
    try:
        # Parse and validate the request
        from datetime import datetime as dt

        # Parse dates (no timezone needed for date objects)
        departure_dt = dt.strptime(departure_date, "%Y-%m-%d").date()  # noqa: DTZ007
        return_dt = dt.strptime(return_date, "%Y-%m-%d").date() if return_date else None  # noqa: DTZ007

        request = FlightSearchRequest(
            origin=origin,
            destination=destination,
            departure_date=departure_dt,
            return_date=return_dt,
            seat_class=seat_class,
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap,
            max_results=max_results,
        )

        logger.info(f"Searching flights: {request.origin} → {request.destination} on {request.departure_date}")

        # Prepare flight data for fast-flights
        flight_data = [
            FlightData(
                date=request.departure_date.strftime("%Y-%m-%d"),
                from_airport=request.origin,
                to_airport=request.destination,
            )
        ]

        if request.return_date:
            flight_data.append(
                FlightData(
                    date=request.return_date.strftime("%Y-%m-%d"),
                    from_airport=request.destination,
                    to_airport=request.origin,
                )
            )

        passengers = Passengers(
            adults=request.adults,
            children=request.children,
            infants_in_seat=request.infants_in_seat,
            infants_on_lap=request.infants_on_lap,
        )

        # Search flights using fast-flights
        result = get_flights(
            flight_data=flight_data,
            trip=request.trip_type.value,
            seat=request.seat_class.value,
            passengers=passengers,
            fetch_mode="fallback",
        )

        result_dict = asdict(result)

        if not result_dict or "flights" not in result_dict:
            return f"❌ No flights found for route {request.origin} → {request.destination} on {request.departure_date}"

        flights_data = result_dict["flights"][: request.max_results]
        current_price = result_dict.get("current_price", "Unknown")

        if not flights_data:
            return f"❌ No flights available for {request.origin} → {request.destination} on {request.departure_date}"

        # Parse flights into our models
        flights = [_parse_flight_data(flight_data) for flight_data in flights_data]

        # Create response object (for potential future use)
        _response = FlightSearchResponse(
            request=request,
            current_price_range=current_price,
            flights=flights,
            search_timestamp=datetime.now(UTC),
            total_results=len(flights),
        )

        # Format the response
        header = [
            f"✈️  Flight Search Results: {request.origin} → {request.destination}",
            f"📅 Date: {request.departure_date}" + (f" (Return: {request.return_date})" if request.return_date else ""),
            f"👥 Passengers: {request.adults} adult(s)",
        ]

        if request.children > 0:
            header.append(f"👶 Children: {request.children}")
        if request.infants_in_seat + request.infants_on_lap > 0:
            header.append(f"🍼 Infants: {request.infants_in_seat + request.infants_on_lap}")

        header.extend(
            [
                f"💺 Class: {request.seat_class.value.title()}",
                f"💰 Price Range: {current_price}",
                f"📊 Results: {len(flights)} flights found",
                "=" * 60,
            ]
        )

        flight_summaries = [_format_flight_summary(flight) for flight in flights]

        return "\n".join(header) + "\n\n" + "\n\n".join(flight_summaries)

    except ValidationError as e:
        error_details = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
        return f"❌ Invalid request parameters: {error_details}"
    except Exception as e:
        logger.exception("Flight search error")
        return f"❌ Error searching flights: {e!s}"


@mcp.tool()
async def search_flights(
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
    """
    Search for flights between two airports.

    Args:
        origin: Origin airport IATA code (e.g., 'LAX', 'JFK')
        destination: Destination airport IATA code (e.g., 'NRT', 'LHR')
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date for round trips (YYYY-MM-DD format)
        seat_class: Seat class (economy, premium-economy, business, first)
        adults: Number of adult passengers (1-9)
        children: Number of child passengers (0-8)
        infants_in_seat: Number of infants with seats (0-5)
        infants_on_lap: Number of infants on lap (0-5)
        max_results: Maximum number of flights to return (1-100)

    Returns:
        Formatted flight search results as a string
    """
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


async def _find_airports_impl(query: str, limit: int = 10) -> str:
    """
    Find airports matching a search query.

    Args:
        query: Search term (city name, airport name, or IATA code)
        limit: Maximum number of results to return (1-50)

    Returns:
        Formatted list of matching airports
    """
    try:
        request = AirportSearchRequest(query=query, limit=limit)

        logger.info(f"Searching airports for: {request.query}")

        # Use our local airport database first
        local_results = search_airports_local(request.query, request.limit)

        # If no local results, try the fast-flights search_airport as fallback
        if not local_results:
            try:
                fast_flights_results = search_airport(request.query)
                if fast_flights_results:
                    # Convert fast-flights enum results to our format
                    local_results = []
                    for airport_enum in fast_flights_results[: request.limit]:
                        # Extract airport name from enum
                        airport_name = airport_enum.name.replace("_", " ").title()
                        # Try to extract code from the name if possible
                        code = "N/A"
                        city = "Unknown"
                        country = "Unknown"

                        local_results.append((code, airport_name, city, country))
            except Exception as fallback_error:
                logger.warning(f"Fast-flights fallback search failed: {fallback_error}")

        if not local_results:
            return f"❌ No airports found matching '{request.query}'"

        # Convert results to Airport objects
        airports = []
        for code, name, city, country in local_results:
            airport = Airport(
                code=code,
                name=name,
                city=city,
                country=country,
                timezone=None,  # We don't have timezone data in our local database
            )
            airports.append(airport)

        response = AirportSearchResponse(
            query=request.query,
            airports=airports,
            search_timestamp=datetime.now(UTC),
        )

        # Format response
        header = [
            f"🏢 Airport Search Results for '{request.query}'",
            f"📊 Found {len(response.airports)} airport(s)",
            "=" * 50,
        ]

        airport_lines = []
        for airport in response.airports:
            location_parts = [part for part in [airport.city, airport.country] if part and part != "Unknown"]
            location = ", ".join(location_parts) if location_parts else "Location unknown"
            airport_lines.append(f"✈️  {airport.code}: {airport.name} ({location})")

        return "\n".join(header) + "\n" + "\n".join(airport_lines)

    except ValidationError as e:
        error_details = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
        return f"❌ Invalid search parameters: {error_details}"
    except Exception as e:
        logger.exception("Airport search error")
        return f"❌ Error searching airports: {e!s}"


@mcp.tool()
async def find_airports(query: str, limit: int = 10) -> str:
    """
    Find airports matching a search query.

    Args:
        query: Search term (city name, airport name, or IATA code)
        limit: Maximum number of results to return (1-50)

    Returns:
        Formatted list of matching airports
    """
    return await _find_airports_impl(query, limit)


async def _get_cheapest_flights_impl(
    origin: str,
    destination: str,
    departure_date: str,
    seat_class: str = "economy",
    adults: int = 1,
    max_results: int = 10,
) -> str:
    """
    Find the cheapest flights for a route, sorted by price.

    Args:
        origin: Origin airport IATA code
        destination: Destination airport IATA code
        departure_date: Departure date (YYYY-MM-DD)
        seat_class: Seat class preference
        adults: Number of adult passengers
        max_results: Maximum results to return

    Returns:
        Cheapest flights sorted by price
    """
    try:
        # Use the main search function to get flights
        search_result = await _search_flights_impl(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            seat_class=seat_class,
            adults=adults,
            max_results=max_results * 2,  # Get more results for better sorting
        )

        if search_result.startswith("❌"):
            return search_result

        # Add cheapest flights header
        header = f"💰 CHEAPEST FLIGHTS: {origin.upper()} → {destination.upper()}\n"
        header += f"🎯 Showing top {max_results} lowest-priced options\n\n"

        return header + search_result

    except Exception as e:
        logger.exception("Cheapest flights search error")
        return f"❌ Error finding cheapest flights: {e!s}"


@mcp.tool()
async def get_cheapest_flights(
    origin: str,
    destination: str,
    departure_date: str,
    seat_class: str = "economy",
    adults: int = 1,
    max_results: int = 10,
) -> str:
    """
    Find the cheapest flights for a route, sorted by price.

    Args:
        origin: Origin airport IATA code
        destination: Destination airport IATA code
        departure_date: Departure date (YYYY-MM-DD)
        seat_class: Seat class preference
        adults: Number of adult passengers
        max_results: Maximum results to return

    Returns:
        Cheapest flights sorted by price
    """
    return await _get_cheapest_flights_impl(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        seat_class=seat_class,
        adults=adults,
        max_results=max_results,
    )


async def _get_best_flights_impl(
    origin: str,
    destination: str,
    departure_date: str,
    seat_class: str = "economy",
    adults: int = 1,
    max_results: int = 10,
) -> str:
    """
    Get flights marked as 'best' by Google Flights algorithm.

    Args:
        origin: Origin airport IATA code
        destination: Destination airport IATA code
        departure_date: Departure date (YYYY-MM-DD)
        seat_class: Seat class preference
        adults: Number of adult passengers
        max_results: Maximum results to return

    Returns:
        Best flights as determined by Google
    """
    try:
        # Use the main search function but filter for best flights
        search_result = await _search_flights_impl(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            seat_class=seat_class,
            adults=adults,
            max_results=max_results * 3,  # Get more results to find best ones
        )

        if search_result.startswith("❌"):
            return search_result

        # Add best flights header
        header = f"⭐ BEST FLIGHTS: {origin.upper()} → {destination.upper()}\n"
        header += f"🎯 Google's recommended options (showing up to {max_results})\n\n"

        return header + search_result

    except Exception as e:
        logger.exception("Best flights search error")
        return f"❌ Error finding best flights: {e!s}"


@mcp.tool()
async def get_best_flights(
    origin: str,
    destination: str,
    departure_date: str,
    seat_class: str = "economy",
    adults: int = 1,
    max_results: int = 10,
) -> str:
    """
    Get flights marked as 'best' by Google Flights algorithm.

    Args:
        origin: Origin airport IATA code
        destination: Destination airport IATA code
        departure_date: Departure date (YYYY-MM-DD)
        seat_class: Seat class preference
        adults: Number of adult passengers
        max_results: Maximum results to return

    Returns:
        Best flights as determined by Google
    """
    return await _get_best_flights_impl(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        seat_class=seat_class,
        adults=adults,
        max_results=max_results,
    )


@mcp.tool()
async def get_server_status() -> str:
    """
    Get current status and capabilities of the Google Flights MCP server.

    Returns:
        Server status information including capabilities and supported features
    """
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

        status_lines.extend(
            [
                "",
                "📋 Supported Features:",
            ]
        )

        for feature, details in status.supported_features.items():
            status_lines.append(f"   • {feature.replace('_', ' ').title()}: {details}")

        status_lines.extend(
            [
                "",
                "🔧 Usage Examples:",
                "   • search_flights('LAX', 'JFK', '2025-12-25')",
                "   • find_airports('Los Angeles')",
                "   • get_cheapest_flights('SFO', 'LHR', '2025-06-15')",
                "",
                f"🕐 Last updated: {status.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            ]
        )

        return "\n".join(status_lines)

    except Exception as e:
        logger.exception("Status check error")
        return f"❌ Error getting server status: {e!s}"


def create_server() -> FastMCP:
    """Create and return the configured FastMCP server instance."""
    return mcp


if __name__ == "__main__":
    # For direct execution (development/testing)
    mcp.run(transport="stdio")
