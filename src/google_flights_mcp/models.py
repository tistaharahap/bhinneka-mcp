"""Pydantic models for Google Flights MCP Server."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class SeatClass(StrEnum):
    """Available seat classes for flight search."""

    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium-economy"
    BUSINESS = "business"
    FIRST = "first"


class TripType(StrEnum):
    """Available trip types."""

    ONE_WAY = "one-way"
    ROUND_TRIP = "round-trip"


class FlightSearchRequest(BaseModel):
    """Flight search request parameters."""

    origin: Annotated[str, Field(min_length=3, max_length=3, description="Origin airport IATA code")]
    destination: Annotated[str, Field(min_length=3, max_length=3, description="Destination airport IATA code")]
    departure_date: Annotated[date, Field(description="Departure date")]
    return_date: Annotated[date | None, Field(default=None, description="Return date for round trips")]
    trip_type: Annotated[TripType, Field(default=TripType.ONE_WAY, description="Type of trip")]
    seat_class: Annotated[SeatClass, Field(default=SeatClass.ECONOMY, description="Seat class preference")]
    adults: Annotated[int, Field(ge=1, le=9, default=1, description="Number of adult passengers")]
    children: Annotated[int, Field(ge=0, le=8, default=0, description="Number of child passengers")]
    infants_in_seat: Annotated[int, Field(ge=0, le=5, default=0, description="Number of infants with seats")]
    infants_on_lap: Annotated[int, Field(ge=0, le=5, default=0, description="Number of infants on lap")]
    max_results: Annotated[int, Field(ge=1, le=100, default=20, description="Maximum number of results")]

    @field_validator("origin", "destination")
    @classmethod
    def validate_airport_codes(cls, v: str) -> str:
        """Validate and normalize airport codes."""
        return v.upper()

    @field_validator("return_date")
    @classmethod
    def validate_return_date(cls, v: date | None, info) -> date | None:
        """Ensure return date is after departure date."""
        if v is not None and "departure_date" in info.data:
            departure = info.data["departure_date"]
            if v <= departure:
                msg = "Return date must be after departure date"
                raise ValueError(msg)
        return v

    @field_validator("trip_type", mode="before")
    @classmethod
    def validate_trip_type(cls, v: str | TripType, info) -> TripType:
        """Auto-detect trip type based on return date."""
        if isinstance(v, str):
            v = TripType(v)

        # Auto-detect based on return_date if not explicitly set
        if "return_date" in info.data:
            return_date = info.data["return_date"]
            if return_date is not None and v == TripType.ONE_WAY:
                return TripType.ROUND_TRIP

        return v


class FlightDetails(BaseModel):
    """Detailed flight information."""

    airline: str
    flight_number: str | None = None
    departure_time: str
    arrival_time: str
    departure_airport: str
    arrival_airport: str
    duration: str
    stops: int
    price: str
    currency: str = "USD"
    is_best: bool = False
    departure_terminal: str | None = None
    arrival_terminal: str | None = None


class Airport(BaseModel):
    """Airport information."""

    code: str
    name: str
    city: str | None = None
    country: str | None = None
    timezone: str | None = None


class FlightSearchResponse(BaseModel):
    """Flight search response."""

    request: FlightSearchRequest
    current_price_range: str | None = None
    flights: list[FlightDetails]
    search_timestamp: datetime
    total_results: int

    @property
    def best_flights(self) -> list[FlightDetails]:
        """Get flights marked as best by Google."""
        return [flight for flight in self.flights if flight.is_best]

    @property
    def cheapest_flights(self) -> list[FlightDetails]:
        """Get flights sorted by price (approximation)."""

        def price_key(flight: FlightDetails) -> float:
            """Extract numeric price for sorting."""
            try:
                # Remove currency symbols and commas, extract number
                price_str = flight.price.replace("$", "").replace(",", "").strip()
                return float(price_str)
            except (ValueError, AttributeError):
                return float("inf")

        return sorted(self.flights, key=price_key)


class AirportSearchRequest(BaseModel):
    """Airport search request."""

    query: Annotated[str, Field(min_length=1, description="Search query (city, airport name, or code)")]
    limit: Annotated[int, Field(ge=1, le=50, default=10, description="Maximum number of results")]


class AirportSearchResponse(BaseModel):
    """Airport search response."""

    query: str
    airports: list[Airport]
    search_timestamp: datetime


class ServerStatus(BaseModel):
    """MCP server status information."""

    service_name: str = "Google Flights MCP"
    version: str = "0.1.0"
    status: str = "online"
    data_source: str = "fast-flights"
    capabilities: list[str] = [
        "flight_search",
        "airport_lookup",
        "price_comparison",
        "multi_passenger_support",
        "all_seat_classes",
    ]
    supported_features: dict[str, str] = {
        "trip_types": "one-way, round-trip",
        "seat_classes": "economy, premium-economy, business, first",
        "passengers": "1-9 adults, 0-8 children, 0-5 infants",
        "coverage": "global flights via Google Flights",
    }
    timestamp: datetime = Field(default_factory=datetime.now)
