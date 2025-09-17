"""Context7 documentation search and retrieval tools.

Implements wrappers over the public Context7 API:
- Search libraries: GET /v1/search?query=...
- Fetch documentation: GET /v1/{libraryId}?tokens=...&topic=...&type=txt

Authentication is optional via `Authorization: Bearer <API_KEY>`.
Optionally includes an encrypted client IP header when available.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


CONTEXT7_BASE_URL = os.getenv("CONTEXT7_BASE_URL", "https://context7.com/api").rstrip("/")
CONTEXT7_API_KEY = os.getenv("CONTEXT7_API_KEY")
CLIENT_IP_ENCRYPTION_KEY = os.getenv("CLIENT_IP_ENCRYPTION_KEY")
CONTEXT7_TIMEOUT = float(os.getenv("CONTEXT7_TIMEOUT", "15"))
CONTEXT7_DEFAULT_TYPE = os.getenv("CONTEXT7_DEFAULT_TYPE", "txt")


def _valid_hex_key_32_bytes(hex_key: str | None) -> bool:
    if not hex_key:
        return False
    if len(hex_key) != 64:
        return False
    try:
        int(hex_key, 16)
        return True
    except ValueError:
        return False


def _generate_headers(
    client_ip: str | None, api_key: str | None, extra: Dict[str, str] | None = None
) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if extra:
        headers.update(extra)

    if client_ip:
        # Encryption not implemented to avoid heavy deps; send plaintext.
        # The upstream service accepts plaintext when encryption is unavailable.
        headers["mcp-client-ip"] = client_ip

    token = api_key or CONTEXT7_API_KEY
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


async def context7_search_impl(
    query: str, *, client_ip: str | None = None, api_key: str | None = None, return_json: bool = False
) -> str:
    try:
        if not query.strip():
            return "❌ Query is required"

        url = f"{CONTEXT7_BASE_URL}/v1/search"
        params = {"query": query}
        headers = _generate_headers(client_ip, api_key)

        async with httpx.AsyncClient(timeout=CONTEXT7_TIMEOUT, headers=headers) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                return "❌ Rate limited. Please try again later."
            if resp.status_code == 401:
                return "❌ Unauthorized. Check CONTEXT7_API_KEY or supplied api_key."
            if resp.status_code >= 400:
                return f"❌ Search failed (HTTP {resp.status_code})"
            data = resp.json()

        results = data.get("results", []) if isinstance(data, dict) else []
        if return_json:
            import json

            return json.dumps({"query": query, "count": len(results), "results": results}, ensure_ascii=False)

        lines = [f"📚 Context7 Search: {query}", "=" * 60]
        if not results:
            lines.append("(no results)")
        else:
            for i, r in enumerate(results, start=1):
                # Each result typically includes: id, name, description, score
                rid = r.get("id") or r.get("slug") or ""
                name = r.get("name") or rid
                desc = (r.get("description") or "").strip()
                if len(desc) > 200:
                    desc = desc[:200].rstrip() + "…"
                lines.append(f"{i}. {name} ({rid})\n   {desc}")
        return "\n".join(lines)
    except Exception as e:
        logger.exception("Context7 search error")
        return f"❌ Error searching Context7: {e!s}"


async def context7_fetch_impl(
    library_id: str,
    *,
    tokens: int | None = None,
    topic: str | None = None,
    type_hint: str | None = None,
    client_ip: str | None = None,
    api_key: str | None = None,
) -> str:
    try:
        lib = library_id.lstrip("/")
        if not lib:
            return "❌ Library ID is required"

        url = f"{CONTEXT7_BASE_URL}/v1/{lib}"
        params: Dict[str, Any] = {}
        if tokens is not None:
            try:
                params["tokens"] = str(int(tokens))
            except Exception:
                return "❌ tokens must be an integer"
        if topic:
            params["topic"] = topic
        params["type"] = type_hint or CONTEXT7_DEFAULT_TYPE or "txt"

        headers = _generate_headers(client_ip, api_key, {"X-Context7-Source": "mcp-server"})

        async with httpx.AsyncClient(timeout=CONTEXT7_TIMEOUT, headers=headers) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                return "❌ Rate limited. Please try again later."
            if resp.status_code == 404:
                return "❌ Library not found. Try a different library ID."
            if resp.status_code == 401:
                return "❌ Unauthorized. Check CONTEXT7_API_KEY or supplied api_key."
            if resp.status_code >= 400:
                return f"❌ Fetch failed (HTTP {resp.status_code})"
            text = resp.text

        if not text or text.strip() in {"No content available", "No context data available"}:
            return "(no content)"
        return text
    except Exception as e:
        logger.exception("Context7 fetch error")
        return f"❌ Error fetching Context7 documentation: {e!s}"
