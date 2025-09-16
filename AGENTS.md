# Repository Guidelines

These guidelines help contributors work consistently across the Bhinneka MCP toolkit.

## Project Structure & Module Organization
- Source code: `src/bhinneka/`
  - `server.py`: FastMCP tools and core logic
  - `cli.py`: Typer CLI entry points (`bhinneka`, `bn`, plus legacy aliases)
  - `models.py`: Pydantic models and enums
  - `airport_data.py`: Local airport search index
- Packaging: `pyproject.toml` (hatchling), entry points under `[project.scripts]`
- Tooling config: `ruff.toml`
- Containerization: `Dockerfile`, `docker-compose.yml`
- Tests (add as needed): `tests/` with `test_*.py`

## Build, Run, and Development Commands
- Install (editable): `pip install -e .`
- Lint: `ruff check` | Format: `ruff format`
- Run (stdio): `uvx bhinneka serve`
- Run (HTTP): `uvx bhinneka serve --transport http --host 0.0.0.0 --port 8000`
- Quick checks: `uvx bhinneka status` | `uvx bhinneka test-search LAX JFK 2025-12-25`
- With rye: `rye sync`, then `rye run ruff check` / `rye run bhinneka serve`
- Docker: `docker build -t bhinneka .` then `docker run -p 8000:8000 bhinneka` or `docker-compose up`

## Coding Style & Naming Conventions
- Language: Python 3.8+ (target runtime), type hints required for new code.
- Formatting & linting: Ruff (line length 120, double quotes, spaces). Run `ruff format && ruff check --fix`.
- Imports: absolute imports only (relative imports are banned by config).
- Indentation: 4 spaces. Docstrings: concise, imperative.
- Naming: modules `snake_case`, functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- CLI may use `rich` printing; avoid `print` elsewhere.

## Testing Guidelines
- Preferred framework: pytest (add `tests/` with `test_*.py`).
- Keep tests fast and deterministic; mock network and external libraries.
- Until unit tests are added, use CLI smoke tests: `uvx bhinneka test-airports "Los Angeles"`.

## Commit & Pull Request Guidelines
- Use Conventional Commits (e.g., `feat: …`, `fix: …`, `refactor: …`).
- Small, focused PRs with clear descriptions; link issues.
- Include reproduction steps, CLI commands, and relevant output/screenshots.
- Update README or docstrings when changing behavior or flags.

## Security & Configuration Tips
- No API keys required; data comes via `fast-flights`.
- Default transport is `stdio`. For HTTP, bind to explicit hosts and consider a reverse proxy; `docker-compose` includes an optional nginx profile.
- Avoid exposing port `8000` publicly without network controls.
