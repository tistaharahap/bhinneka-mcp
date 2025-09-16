# Google Flights MCP Server

A FastMCP server that provides Google Flights data access via Model Context Protocol (MCP). Search for flights, find airports, and get pricing information through standardized MCP tools.

## Features

- **Flight Search**: Find flights between airports with flexible search criteria
- **Airport Lookup**: Search airports by code, name, or city with comprehensive database
- **Price Optimization**: Get cheapest flight options sorted by price
- **Best Flights**: Access Google's recommended flight selections
- **Multiple Transports**: Support for stdio (development) and HTTP (production) modes
- **CLI Interface**: Built-in testing and management commands

## Installation

### Using uvx (Recommended)

```bash
# Install and run directly with uvx
uvx google-flights-mcp --help
```

### Using pip

```bash
pip install google-flights-mcp
```

## Quick Start with uvx

### MCP Server Modes

```bash
# Development mode (stdio transport for MCP clients)
uvx google-flights-mcp dev

# Production mode (HTTP server for remote access)
uvx google-flights-mcp serve --host 0.0.0.0 --port 8000

# Check server status and capabilities
uvx google-flights-mcp status
```

### Testing Commands

```bash
# Test flight search
uvx google-flights-mcp test-search LAX JFK 2025-12-25

# Test airport search
uvx google-flights-mcp test-airports "Los Angeles"

# Show version information
uvx google-flights-mcp version
```

### Short Command Alias

The package also provides a shorter `gf` command:

```bash
# All commands work with the shorter alias
uvx google-flights-mcp dev
# is equivalent to
uvx --from google-flights-mcp gf dev
```

## MCP Integration

### With MCP Inspector

For development and testing with MCP Inspector:

```bash
uvx google-flights-mcp dev
```

Then connect your MCP client to the stdio transport.

### HTTP Server Mode

For production use or remote MCP clients:

```bash
uvx google-flights-mcp serve --host 0.0.0.0 --port 8000
```

MCP clients can connect to: `http://your-server:8000/mcp`

## Available MCP Tools

### `search_flights`
Search for flights between two airports.

**Parameters:**
- `origin` (string): Origin airport code (e.g., "LAX")
- `destination` (string): Destination airport code (e.g., "JFK")
- `departure_date` (string): Departure date in YYYY-MM-DD format
- `return_date` (string, optional): Return date for round-trip flights
- `seat_class` (string): Seat class - "economy", "premium_economy", "business", "first"
- `adults` (integer): Number of adult passengers (default: 1)
- `children` (integer, optional): Number of child passengers
- `infants` (integer, optional): Number of infant passengers
- `max_results` (integer): Maximum results to return (default: 6)

### `find_airports`
Search for airports by code, name, or city.

**Parameters:**
- `query` (string): Search query (airport code, name, or city)
- `limit` (integer): Maximum results to return (default: 10)

### `get_cheapest_flights`
Get flights sorted by price (lowest first).

**Parameters:** Same as `search_flights`

### `get_best_flights`
Get Google's recommended "best" flights balancing price, duration, and convenience.

**Parameters:** Same as `search_flights`

### `get_server_status`
Get server status and capabilities information.

**Parameters:** None

## Development Setup

### Requirements
- Python 3.8+
- rye (recommended) or pip

### Setup with rye

```bash
# Clone the repository
git clone <repository-url>
cd google-flights-mcp

# Install dependencies
rye sync

# Run in development mode
rye run python -m google_flights_mcp.cli dev

# Run tests
rye run python -m google_flights_mcp.cli test-search LAX JFK 2025-12-25

# Code formatting and linting
rye run ruff check
rye run ruff format
```

## Configuration

### Transport Options

- **stdio**: For MCP Inspector and direct client integration
- **streamable-http**: For remote access and production deployments

### Environment Variables

The server uses standard MCP environment variables and configurations. No API keys are required as it uses public Google Flights data via the fast-flights library.

## Data Source

This server uses the [fast-flights](https://pypi.org/project/fast-flights/) library to access Google Flights data. The library provides real-time flight information without requiring API keys.

## License

[Add your license information here]