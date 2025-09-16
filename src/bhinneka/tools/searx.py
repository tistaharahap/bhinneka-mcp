"""SearXNG search implementation for MCP tools."""

from __future__ import annotations

import os
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# Environment-driven configuration
SEARXNG_BASE_URL = os.getenv("SEARXNG_BASE_URL", "").rstrip("/")
SEARXNG_TIMEOUT = float(os.getenv("SEARXNG_TIMEOUT", "8"))
SEARXNG_MAX_RESULTS_DEFAULT = int(os.getenv("SEARXNG_MAX_RESULTS", "10"))
SEARXNG_LANGUAGE_DEFAULT = os.getenv("SEARXNG_LANGUAGE", "en")


async def searx_search_impl(
    query: str,
    *,
    category: str | None = None,
    engines: str | None = None,
    language: str | None = None,
    time_range: str | None = None,
    safesearch: int | None = 1,
    max_results: int | None = None,
    return_json: bool = False,
) -> str:
    """Query SearXNG JSON API and return formatted or JSON string."""
    try:
        if not SEARXNG_BASE_URL:
            return "❌ SearXNG base URL not configured. Set SEARXNG_BASE_URL."

        url = f"{SEARXNG_BASE_URL}/search"
        params: dict[str, Any] = {
            "q": query,
            "format": "json",
        }
        lang = (language or SEARXNG_LANGUAGE_DEFAULT or "en").strip()
        if lang:
            params["language"] = lang
        if category:
            params["categories"] = category
        if engines:
            params["engines"] = engines
        if time_range:
            params["time_range"] = time_range
        if safesearch is not None:
            params["safesearch"] = str(int(safesearch))

        limit = max_results or SEARXNG_MAX_RESULTS_DEFAULT

        async with httpx.AsyncClient(timeout=SEARXNG_TIMEOUT, headers={"User-Agent": "bhinneka/0.1"}) as client:
            resp = await client.get(url, params=params)
            if resp.status_code >= 400:
                return f"❌ SearXNG error {resp.status_code}: {resp.text[:200]}"
            data = resp.json()

        results = data.get("results", []) if isinstance(data, dict) else []
        normalized: list[dict[str, str]] = []
        for item in results[:limit]:
            title = item.get("title") or item.get("pretty_url") or "(no title)"
            url_out = item.get("url") or item.get("href") or ""
            snippet = item.get("content") or item.get("snippet") or ""
            engine = item.get("engine") or item.get("source") or ""
            score = item.get("score")
            norm: dict[str, str] = {
                "title": str(title),
                "url": str(url_out),
                "snippet": str(snippet),
                "engine": str(engine),
            }
            if score is not None:
                norm["score"] = str(score)
            if category == "images":
                img_src = item.get("img_src") or item.get("thumbnail_src")
                if img_src:
                    norm["image"] = str(img_src)
            normalized.append(norm)

        if return_json:
            import json

            return json.dumps({"query": query, "count": len(normalized), "results": normalized}, ensure_ascii=False)

        header = [
            f"🔎 SearXNG Search: {query}",
            f"🌐 Category: {category or 'general'} | Lang: {lang} | Max: {limit}",
            "=" * 60,
        ]
        lines: list[str] = []
        for idx, r in enumerate(normalized, start=1):
            if category == "images" and r.get("image"):
                lines.append(
                    f"{idx}. {r['title']}\n   {r['url']}\n   {r.get('image')}\n   {r.get('engine','')}"
                )
            else:
                snippet_out = r.get("snippet", "")
                if len(snippet_out) > 300:
                    snippet_out = snippet_out[:300].rstrip() + "…"
                lines.append(
                    f"{idx}. {r['title']}\n   {r['url']}\n   {snippet_out}\n   {r.get('engine','')}"
                )
        if not lines:
            lines.append("(no results)")
        return "\n".join(header + lines)
    except Exception as e:  # noqa: BLE001
        logger.exception("SearXNG search error")
        return f"❌ Error querying SearXNG: {e!s}"

