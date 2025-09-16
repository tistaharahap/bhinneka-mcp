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

### Using Docker (For Remote Deployment)

```bash
# Build and run with Docker
docker build -t google-flights-mcp .
docker run -p 8000:8000 google-flights-mcp

# Or use docker-compose for easier management
docker-compose up
```

## Quick Start with uvx

### MCP Server Modes

```bash
# Default mode (stdio transport for Claude Desktop and MCP clients)
uvx google-flights-mcp serve

# HTTP mode (for remote access)
uvx google-flights-mcp serve --transport http --host 0.0.0.0 --port 8000

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
uvx google-flights-mcp serve
# is equivalent to
uvx --from google-flights-mcp gf serve
```

## MCP Integration

### With MCP Inspector

For development and testing with MCP Inspector:

```bash
uvx google-flights-mcp serve
```

Then connect your MCP client to the stdio transport.

### HTTP Server Mode

For production use or remote MCP clients:

```bash
uvx google-flights-mcp serve --transport http --host 0.0.0.0 --port 8000
```

MCP clients can connect to: `http://your-server:8000/mcp`

### With Claude Desktop

To use this MCP server with Claude Desktop, add the following configuration to your Claude Desktop settings:

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "uvx",
      "args": [
        "google-flights-mcp",
        "serve"
      ]
    }
  }
}
```

This configuration will:
- Automatically install the latest version using `uvx`
- Run the server with stdio transport (default for Claude Desktop)
- Make flight search tools available in Claude Desktop

After adding this configuration, restart Claude Desktop and you'll have access to all the flight search tools directly in your conversations.

#### Alternative Configuration with HTTP Transport

For advanced users who prefer HTTP transport for remote access:

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "uvx",
      "args": [
        "google-flights-mcp",
        "serve",
        "--transport",
        "http",
        "--host",
        "127.0.0.1",
        "--port",
        "8000"
      ]
    }
  }
}
```

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
git clone https://github.com/tistaharahap/google-flights-mcp
cd google-flights-mcp

# Install dependencies
rye sync

# Run the MCP server
rye run python -m google_flights_mcp.cli serve

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

## Docker Deployment

### Building and Running with Docker

```bash
# Build the Docker image
docker build -t google-flights-mcp .

# Run the container
docker run -d \
  --name google-flights-mcp \
  -p 8000:8000 \
  --restart unless-stopped \
  google-flights-mcp

# Check container logs
docker logs google-flights-mcp

# Stop the container
docker stop google-flights-mcp
```

### Using Docker Compose (Recommended)

The repository includes a `docker-compose.yml` file for easier deployment:

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

### Production Deployment with Nginx

For production deployments, use the nginx profile for reverse proxy and SSL termination:

```bash
# Start with nginx reverse proxy
docker-compose --profile production up -d

# This will start both the MCP server and nginx
# Configure SSL certificates in ./ssl/ directory
# Customize nginx.conf for your domain and SSL setup
```

### Docker Configuration

The Docker setup includes:

- **Multi-stage build** for optimized image size
- **Non-root user** for enhanced security
- **Health checks** for container monitoring
- **HTTP transport** configured for remote access
- **Port 8000** exposed for MCP client connections

### Environment Variables

You can customize the deployment using environment variables:

```bash
# Custom host and port
docker run -p 9000:9000 \
  -e GOOGLE_FLIGHTS_HOST=0.0.0.0 \
  -e GOOGLE_FLIGHTS_PORT=9000 \
  google-flights-mcp

# Or in docker-compose.yml:
environment:
  - GOOGLE_FLIGHTS_HOST=0.0.0.0
  - GOOGLE_FLIGHTS_PORT=8000
```

### Connecting to Dockerized MCP Server

When running in Docker, the server is accessible via HTTP transport:

- **Local access**: `http://localhost:8000/mcp`
- **Remote access**: `http://your-server-ip:8000/mcp`

Configure your MCP client to connect to the HTTP endpoint instead of stdio transport.

## Data Source

This server uses the [fast-flights](https://pypi.org/project/fast-flights/) library to access Google Flights data. The library provides real-time flight information without requiring API keys.

## License

[Add your license information here]