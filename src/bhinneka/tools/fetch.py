"""Safe URL fetching and text extraction utilities for MCP tools.

Default behavior is a static fetch (no JS), with HTML stripped to readable text.
Optionally supports JS rendering via Playwright when explicitly enabled.
"""

from __future__ import annotations

import asyncio
import logging
import re
import socket
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from ipaddress import ip_address, IPv4Address, IPv6Address
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)


SAFE_SCHEMES = {"http", "https"}


@dataclass
class FetchResult:
    url_final: str
    status_code: int
    content_type: str | None
    encoding: str | None
    bytes_downloaded: int
    title: str | None
    description: str | None
    language: str | None
    text: str | None
    links: list[dict[str, str]] | None
    notes: list[str]


def _is_ip_private(addr: str) -> bool:
    try:
        ip = ip_address(addr)
    except ValueError:
        return False
    if isinstance(ip, (IPv4Address, IPv6Address)):
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )
    return False


def _host_resolves_to_private(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:  # noqa: BLE001
        # If resolution fails, be conservative and block
        return True
    addrs: set[str] = set()
    for info in infos:
        sockaddr = info[4]
        if isinstance(sockaddr, tuple) and sockaddr:
            addrs.add(sockaddr[0])
    return any(_is_ip_private(a) for a in addrs)


def _is_url_safe(url: str) -> tuple[bool, str | None]:
    try:
        p = urlparse(url)
    except Exception as e:  # noqa: BLE001
        return False, f"Invalid URL: {e!s}"
    if p.scheme not in SAFE_SCHEMES:
        return False, "Only http(s) URLs are allowed"
    host = p.hostname or ""
    if not host:
        return False, "URL missing hostname"
    if host.lower() in {"localhost", "localhost.localdomain"}:
        return False, "Access to localhost is blocked"
    # Literal IP hosts
    try:
        if _is_ip_private(host):
            return False, "Access to private/loopback addresses is blocked"
    except Exception:
        pass
    # DNS resolution check
    if _host_resolves_to_private(host):
        return False, "Host resolves to private/loopback address (blocked)"
    return True, None


class _HTMLTextExtractor(HTMLParser):
    def __init__(self, base_url: str, collect_links: bool) -> None:
        super().__init__(convert_charrefs=False)
        self.base_url = base_url
        self.collect_links = collect_links
        self._texts: list[str] = []
        self._chunks: list[str] = []
        self._in_script = 0
        self._in_style = 0
        self._title_parts: list[str] = []
        self._in_title = 0
        self._lang: str | None = None
        self._description: str | None = None
        self._links: list[dict[str, str]] = []
        self.script_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: D401
        if tag == "script":
            self._in_script += 1
            self.script_count += 1
            return
        if tag == "style":
            self._in_style += 1
            return
        if tag == "title":
            self._in_title += 1
        if tag == "html":
            # Look for lang attribute
            for k, v in attrs:
                if k.lower() == "lang" and v:
                    self._lang = v.strip()
        if tag == "meta":
            name = None
            content = None
            http_equiv = None
            prop = None
            for k, v in attrs:
                kl = k.lower()
                if kl == "name":
                    name = (v or "").lower()
                elif kl == "content":
                    content = v
                elif kl == "http-equiv":
                    http_equiv = (v or "").lower()
                elif kl == "property":
                    prop = (v or "").lower()
            if content:
                if name == "description" or prop == "og:description":
                    self._description = content
                if http_equiv == "content-language" and not self._lang:
                    self._lang = content.split(",")[0].strip()
        if self.collect_links and tag == "a":
            href = None
            text = None
            for k, v in attrs:
                kl = k.lower()
                if kl == "href":
                    href = v
                elif kl == "title":
                    text = v
            if href:
                abs_url = urljoin(self.base_url, href)
                self._links.append({"url": abs_url, "text": text or ""})

    def handle_endtag(self, tag: str) -> None:  # noqa: D401
        if tag == "script" and self._in_script:
            self._in_script -= 1
            return
        if tag == "style" and self._in_style:
            self._in_style -= 1
            return
        if tag == "title" and self._in_title:
            self._in_title -= 1

    def handle_data(self, data: str) -> None:  # noqa: D401
        if self._in_script or self._in_style:
            return
        if self._in_title:
            self._title_parts.append(data)
            return
        # Collect visible text
        self._chunks.append(data)

    def _finish(self) -> None:
        # Normalize whitespace and join
        text = unescape("".join(self._chunks))
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            self._texts.append(text)

    @property
    def text(self) -> str:
        if not self._texts:
            self._finish()
        return "\n".join(self._texts).strip()

    @property
    def title(self) -> str | None:
        t = unescape("".join(self._title_parts)).strip()
        return t or None

    @property
    def description(self) -> str | None:  # noqa: D401
        return self._description

    @property
    def language(self) -> str | None:  # noqa: D401
        return self._lang

    @property
    def links(self) -> list[dict[str, str]]:  # noqa: D401
        return self._links


async def _fetch_static(
    url: str,
    *,
    timeout: float,
    max_bytes: int,
    follow_redirects: bool,
    user_agent: str,
) -> tuple[str, int, str | None, str | None, bytes]:
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=follow_redirects,
        headers={"User-Agent": user_agent},
    ) as client:
        resp = await client.get(url)
        ctype = resp.headers.get("content-type")
        encoding = resp.encoding
        final_url = str(resp.url)
        # Stream and enforce max_bytes
        data = b""
        async for chunk in resp.aiter_bytes():
            data += chunk
            if len(data) >= max_bytes:
                data = data[:max_bytes]
                break
        return final_url, resp.status_code, ctype, encoding, data


async def _render_with_playwright(url: str, timeout: float, user_agent: str) -> tuple[str, str]:
    try:
        from playwright.async_api import async_playwright  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Playwright not available: {e!s}")

    async with async_playwright() as p:  # type: ignore
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(user_agent=user_agent)
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=int(timeout * 1000))
            # Try to settle a bit more, but keep bounded
            try:
                await page.wait_for_load_state("networkidle", timeout=int(timeout * 1000))
            except Exception:  # noqa: BLE001
                pass
            html = await page.content()
            final_url = page.url
            await context.close()
            return final_url, html
        finally:
            await browser.close()


def _summarize(
    res: FetchResult,
    *,
    max_chars: int = 2000,
) -> str:
    header = [
        f"🔗 URL: {res.url_final}",
        f"📄 Status: {res.status_code} | Type: {res.content_type or 'unknown'} | Bytes: {res.bytes_downloaded}",
    ]
    meta = []
    if res.title:
        meta.append(f"Title: {res.title}")
    if res.description:
        meta.append(f"Description: {res.description}")
    if res.language:
        meta.append(f"Lang: {res.language}")
    if meta:
        header.append(" • ".join(meta))
    if res.notes:
        for n in res.notes:
            header.append(f"⚠️ {n}")
    body = res.text or "(no text)"
    if len(body) > max_chars:
        body = body[:max_chars].rstrip() + "…"
    return "\n".join(header + ["", body])


async def fetch_url_impl(
    url: str,
    *,
    text_only: bool = True,
    render_js: bool = False,
    timeout: float = 30.0,
    max_bytes: int = 2_000_000,
    follow_redirects: bool = True,
    extract_links: bool = False,
    return_json: bool = False,
) -> str:
    """Fetch a URL with safe defaults and optional JS rendering.

    - Blocks non-http(s), localhost, and private networks.
    - By default, strips HTML/CSS/JS and returns readable text.
    - If ``render_js`` is True, uses Playwright to render first.
    """
    try:
        ok, why = _is_url_safe(url)
        if not ok:
            return f"❌ {why}"

        user_agent = "bhinneka/0.2 fetch"
        notes: list[str] = []

        final_url: str
        status: int
        ctype: str | None
        encoding: str | None
        raw: bytes

        if render_js:
            try:
                final_url, html = await _render_with_playwright(url, timeout=timeout, user_agent=user_agent)
                status = 200
                ctype = "text/html; charset=utf-8"
                encoding = "utf-8"
                raw = html.encode("utf-8", errors="ignore")
            except Exception as e:  # noqa: BLE001
                return f"❌ JS rendering failed: {e!s}"
        else:
            final_url, status, ctype, encoding, raw = await _fetch_static(
                url,
                timeout=timeout,
                max_bytes=max_bytes,
                follow_redirects=follow_redirects,
                user_agent=user_agent,
            )

        content_type = (ctype or "").lower()
        text_out: str | None = None
        title: str | None = None
        description: str | None = None
        language: str | None = None
        links: list[dict[str, str]] | None = None

        if content_type.startswith("text/html"):
            html_text = raw.decode(encoding or "utf-8", errors="ignore")
            parser = _HTMLTextExtractor(final_url, collect_links=extract_links)
            parser.feed(html_text)
            text_out = parser.text if text_only else html_text
            title = parser.title
            description = parser.description
            language = parser.language
            if extract_links:
                links = parser.links

            # Heuristic for SPA hint
            if not render_js:
                if len(text_out or "") < 200 and parser.script_count >= 5:
                    notes.append("Content looks dynamic; try render_js=true for SPA pages")

        elif content_type.startswith("application/json") or content_type.startswith("text/plain"):
            # Pretty print JSON, or just text
            try:
                if content_type.startswith("application/json"):
                    import json

                    obj = json.loads(raw.decode(encoding or "utf-8", errors="ignore"))
                    text_out = json.dumps(obj, ensure_ascii=False, indent=2)
                else:
                    text_out = raw.decode(encoding or "utf-8", errors="ignore")
            except Exception:  # noqa: BLE001
                text_out = raw.decode(encoding or "utf-8", errors="ignore")
        else:
            notes.append("Unsupported content-type for text extraction; returning headers only")

        result = FetchResult(
            url_final=final_url,
            status_code=status,
            content_type=ctype,
            encoding=encoding,
            bytes_downloaded=len(raw),
            title=title,
            description=description,
            language=language,
            text=text_out,
            links=links,
            notes=notes,
        )

        if return_json:
            import json

            payload: dict[str, Any] = {
                "url_final": result.url_final,
                "status_code": result.status_code,
                "content_type": result.content_type,
                "encoding": result.encoding,
                "bytes_downloaded": result.bytes_downloaded,
                "title": result.title,
                "description": result.description,
                "language": result.language,
                "text": result.text,
                "links": result.links,
                "notes": result.notes,
            }
            return json.dumps(payload, ensure_ascii=False)

        return _summarize(result)
    except Exception as e:  # noqa: BLE001
        logger.exception("fetch_url_impl error")
        return f"❌ Error fetching URL: {e!s}"
