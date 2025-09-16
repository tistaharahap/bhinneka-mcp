# syntax=docker/dockerfile:1

#=== Build stage: Install dependencies and create virtual environment ===#
FROM python:3.13-slim AS builder

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app

# Create virtual environment
RUN python -m venv /app/venv

# Copy dependency files first for better layer caching
COPY pyproject.toml README.md ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy source code and install the package
COPY src/ ./src/
RUN pip install --no-cache-dir .

#=== Final stage: Create minimal runtime image ===#
FROM python:3.13-slim AS runtime

# Create non-root user for security
RUN groupadd --gid 1000 mcp && \
    useradd --uid 1000 --gid mcp --shell /bin/bash --create-home mcp

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/venv/bin:$PATH"

# Copy virtual environment from builder stage
COPY --from=builder --chown=mcp:mcp /app/venv /app/venv

# Change to non-root user
USER mcp

# Expose port for HTTP transport
EXPOSE 8000

# Health check to ensure the server is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost', 8000)); s.close()" || exit 1

# Default command - run MCP server with HTTP transport
CMD ["google-flights-mcp", "serve", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]