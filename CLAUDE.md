# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bhinneka MCP Toolkit — A FastMCP server that provides Google Flights utilities and SearXNG web search via Model Context Protocol. The server uses the `fast-flights` library for flights and SearXNG's JSON API for web search.

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
rye run python -m bhinneka.cli dev

# Production mode (HTTP transport for remote access)
rye run python -m bhinneka.cli serve --host 0.0.0.0 --port 8000

# Using installed CLI shortcuts
rye run bhinneka dev
rye run bn dev
```

### Testing
```bash
# Test flight search functionality
rye run python -m bhinneka.cli test-search LAX JFK 2025-12-25

# Test airport search functionality  
rye run python -m bhinneka.cli test-airports "Los Angeles"

# Check server status and capabilities
rye run python -m bhinneka.cli status
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

**`server.py`** - Core MCP server with namespaced tools (flights_* and searx_*). Logic lives under `bhinneka/tools`.
**`tools/flights.py`** - `_search_flights_impl()`, `_find_airports_impl()`, `_get_cheapest_flights_impl()`, `_get_best_flights_impl()`
**`tools/searx.py`** - `searx_search_impl()` JSON-based web search

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
