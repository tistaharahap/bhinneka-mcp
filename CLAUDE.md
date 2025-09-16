# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Google Flights MCP Server - A FastMCP server that provides Google Flights data access via Model Context Protocol. The server uses the `fast-flights` library to fetch flight data and presents it through standardized MCP tools.

## Development Commands

### Package Management
```bash
# Install dependencies and sync environment
rye sync

# Run commands within the virtual environment
rye run <command>
```

### Running the Server
```bash
# Development mode (stdio transport for MCP Inspector)
rye run python -m google_flights_mcp.cli dev

# Production mode (HTTP transport for remote access)
rye run python -m google_flights_mcp.cli serve --host 0.0.0.0 --port 8000

# Using installed CLI shortcuts
rye run google-flights-mcp dev
rye run gf dev
```

### Testing
```bash
# Test flight search functionality
rye run python -m google_flights_mcp.cli test-search LAX JFK 2025-12-25

# Test airport search functionality  
rye run python -m google_flights_mcp.cli test-airports "Los Angeles"

# Check server status and capabilities
rye run python -m google_flights_mcp.cli status
```

### Code Quality
```bash
# Run linting with ruff
rye run ruff check

# Auto-fix linting issues
rye run ruff check --fix

# Format code
rye run ruff format
```

## Architecture

### Core Architecture Pattern
The codebase follows a separation pattern between MCP tool decorators and implementation functions to avoid FastMCP's `'FunctionTool' object is not callable` issues:

- **Implementation Functions**: `_function_name_impl()` - Contains core business logic
- **MCP Tool Wrappers**: `function_name()` - Decorated with `@mcp.tool()`, calls implementation
- **CLI Integration**: Uses implementation functions directly to avoid MCP decorator conflicts

### Key Modules

**`server.py`** - Core MCP server with flight search tools:
- `_search_flights_impl()` / `search_flights()` - General flight search
- `_find_airports_impl()` / `find_airports()` - Airport lookup with local database
- `_get_cheapest_flights_impl()` / `get_cheapest_flights()` - Price-optimized search
- `_get_best_flights_impl()` / `get_best_flights()` - Google's recommended flights

**`models.py`** - Pydantic data models for validation and type safety

**`cli.py`** - Typer-based CLI with Rich formatting for both development and production use

**`airport_data.py`** - Local airport database with intelligent search to supplement fast-flights limitations

### Data Flow
1. CLI/MCP tool receives request parameters
2. Implementation function validates and processes parameters  
3. `fast-flights` library queries Google Flights
4. Response data is parsed with safe type conversion (`_safe_int_conversion`, `_safe_bool_conversion`)
5. Results formatted for human-readable output
6. Local airport database provides fallback for airport searches

### Transport Modes
- **stdio**: Development mode for MCP Inspector integration
- **streamable-http**: Production mode for remote MCP client access

### Critical Implementation Notes
- Always use implementation functions (`_*_impl`) when calling from other MCP tools or CLI
- MCP decorated functions cannot be called directly by other MCP functions
- Safe type conversion is essential due to inconsistent fast-flights API response types
- Local airport database provides better search results than fast-flights' limited airport search