"""First-class web_fetch / web_search for SafeClaw agents.

Providers (search):
  1. Tavily if TAVILY_API_KEY is set
  2. Brave if BRAVE_SEARCH_API_KEY is set
  3. DuckDuckGo Instant Answer API (no key; not a full SERP)

Fail Fast: empty query/URL, non-http(s), private/link-local targets,
network errors, and zero useful search hits (with actionable hint).
"""

from __future__ import annotations

import html
import ipaddress
import logging
import os
import re
import socket
from typing import Any, Callable, List, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_S = 20.0
DEFAULT_FETCH_MAX_CHARS = 12_000
DEFAULT_SEARCH_MAX_RESULTS = 5
_USER_AGENT = "SafeClaw/1.0 (+https://github.com/a476678244/python_gallery)"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


class WebToolError(ValueError):
    """Fail Fast error for web tools (surfaces as tool failure)."""


def _client_factory() -> httpx.Client:
    return httpx.Client(
        timeout=DEFAULT_TIMEOUT_S,
        follow_redirects=True,
        headers={"User-Agent": _USER_AGENT, "Accept": "*/*"},
    )


def validate_public_http_url(url: str) -> str:
    """Validate http(s) URL and reject private / loopback / link-local hosts."""
    raw = (url or "").strip()
    if not raw:
        raise WebToolError(
            "[web_fetch] URL is required\n"
            "  Actual: empty/whitespace"
        )
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise WebToolError(
            "[web_fetch] Only http/https URLs are allowed\n"
            f"  Actual scheme: {parsed.scheme!r}\n"
            f"  URL: {raw}"
        )
    host = parsed.hostname
    if not host:
        raise WebToolError(
            f"[web_fetch] URL missing hostname\n"
            f"  URL: {raw}"
        )
    host_l = host.lower()
    if host_l in {"localhost", "0.0.0.0"} or host_l.endswith(".local"):
        raise WebToolError(
            f"[web_fetch] Blocked host (SSRF)\n"
            f"  Host: {host}\n"
            f"  URL: {raw}"
        )
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise WebToolError(
            f"[web_fetch] DNS resolution failed\n"
            f"  Host: {host}\n"
            f"  Error: {exc}"
        ) from exc
    if not infos:
        raise WebToolError(
            f"[web_fetch] DNS returned no addresses\n"
            f"  Host: {host}"
        )
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            raise WebToolError(
                f"[web_fetch] Blocked non-public IP (SSRF)\n"
                f"  Host: {host}\n"
                f"  Resolved: {ip_str}\n"
                f"  URL: {raw}"
            )
    return raw


def _html_to_text(body: str) -> str:
    text = re.sub(
        r"(?is)<(script|style|noscript).*?>.*?</\1>",
        " ",
        body,
    )
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def fetch_url(
    url: str,
    *,
    max_chars: int = DEFAULT_FETCH_MAX_CHARS,
    client: Optional[httpx.Client] = None,
) -> str:
    """GET a public URL and return truncated text content."""
    safe_url = validate_public_http_url(url)
    limit = max(500, min(int(max_chars or DEFAULT_FETCH_MAX_CHARS), 50_000))
    owns = client is None
    http = client or _client_factory()
    try:
        resp = http.get(safe_url)
    except httpx.HTTPError as exc:
        raise WebToolError(
            f"[web_fetch] Request failed\n"
            f"  URL: {safe_url}\n"
            f"  Error: {type(exc).__name__}: {exc}"
        ) from exc
    finally:
        if owns:
            http.close()

    ctype = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
    # Cap raw bytes before decode
    raw = resp.content[: limit * 4]
    try:
        body = raw.decode(resp.encoding or "utf-8", errors="replace")
    except LookupError:
        body = raw.decode("utf-8", errors="replace")

    if "html" in ctype or body.lstrip()[:15].lower().startswith("<!doctype") or body.lstrip()[:6].lower().startswith("<html"):
        text = _html_to_text(body)
    else:
        text = body.strip()

    if len(text) > limit:
        text = text[: limit - 3] + "..."

    header = (
        f"URL: {safe_url}\n"
        f"Status: {resp.status_code}\n"
        f"Content-Type: {ctype or 'unknown'}\n"
        f"Chars: {len(text)}\n\n"
    )
    if resp.status_code >= 400:
        raise WebToolError(
            f"[web_fetch] HTTP error\n"
            f"  URL: {safe_url}\n"
            f"  Status: {resp.status_code}\n"
            f"  Body preview: {text[:300]}"
        )
    if not text:
        raise WebToolError(
            f"[web_fetch] Empty body after extract\n"
            f"  URL: {safe_url}\n"
            f"  Status: {resp.status_code}\n"
            f"  Content-Type: {ctype or 'unknown'}"
        )
    return header + text


def _format_results(query: str, provider: str, items: List[dict]) -> str:
    lines = [
        f"Web search ({provider}) for: {query}",
        f"Results: {len(items)}",
        "",
    ]
    for i, item in enumerate(items, 1):
        title = (item.get("title") or "").strip() or "(no title)"
        url = (item.get("url") or "").strip()
        snippet = (item.get("snippet") or "").strip().replace("\n", " ")
        if len(snippet) > 280:
            snippet = snippet[:277] + "..."
        lines.append(f"{i}. {title}")
        if url:
            lines.append(f"   {url}")
        if snippet:
            lines.append(f"   {snippet}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _search_tavily(
    query: str, max_results: int, client: httpx.Client, api_key: str
) -> List[dict]:
    resp = client.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": False,
        },
    )
    if resp.status_code >= 400:
        raise WebToolError(
            f"[web_search] Tavily HTTP error\n"
            f"  Status: {resp.status_code}\n"
            f"  Body: {resp.text[:400]}"
        )
    data = resp.json()
    out: List[dict] = []
    for row in data.get("results") or []:
        out.append(
            {
                "title": row.get("title") or "",
                "url": row.get("url") or "",
                "snippet": row.get("content") or row.get("snippet") or "",
            }
        )
    return out


def _search_brave(
    query: str, max_results: int, client: httpx.Client, api_key: str
) -> List[dict]:
    resp = client.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": max_results},
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
        },
    )
    if resp.status_code >= 400:
        raise WebToolError(
            f"[web_search] Brave HTTP error\n"
            f"  Status: {resp.status_code}\n"
            f"  Body: {resp.text[:400]}"
        )
    data = resp.json()
    out: List[dict] = []
    for row in (data.get("web") or {}).get("results") or []:
        out.append(
            {
                "title": row.get("title") or "",
                "url": row.get("url") or "",
                "snippet": row.get("description") or "",
            }
        )
    return out


def _flatten_ddg_topics(topics: Any, out: List[dict], limit: int) -> None:
    if not isinstance(topics, list):
        return
    for topic in topics:
        if len(out) >= limit:
            return
        if not isinstance(topic, dict):
            continue
        if "Topics" in topic:
            _flatten_ddg_topics(topic.get("Topics"), out, limit)
            continue
        text = (topic.get("Text") or "").strip()
        url = (topic.get("FirstURL") or "").strip()
        if not text and not url:
            continue
        title = text.split(" - ", 1)[0] if text else url
        out.append({"title": title, "url": url, "snippet": text})


def _search_duckduckgo_ia(
    query: str, max_results: int, client: httpx.Client
) -> List[dict]:
    resp = client.get(
        "https://api.duckduckgo.com/",
        params={
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        },
    )
    if resp.status_code >= 400:
        raise WebToolError(
            f"[web_search] DuckDuckGo Instant Answer HTTP error\n"
            f"  Status: {resp.status_code}\n"
            f"  Body: {resp.text[:400]}"
        )
    data = resp.json()
    out: List[dict] = []
    abstract = (data.get("AbstractText") or "").strip()
    abstract_url = (data.get("AbstractURL") or "").strip()
    heading = (data.get("Heading") or "").strip()
    if abstract:
        out.append(
            {
                "title": heading or query,
                "url": abstract_url,
                "snippet": abstract,
            }
        )
    answer = (data.get("Answer") or "").strip()
    if answer and len(out) < max_results:
        out.append(
            {
                "title": heading or "Instant answer",
                "url": abstract_url,
                "snippet": answer,
            }
        )
    _flatten_ddg_topics(data.get("RelatedTopics"), out, max_results)
    return out[:max_results]


def resolve_search_provider(
    env: Optional[Callable[[str], Optional[str]]] = None,
) -> tuple[str, Optional[str]]:
    """Return (provider, api_key). getenv-compatible env callable for tests."""
    get = env or os.getenv
    forced = (get("SAFECLAW_WEB_SEARCH_PROVIDER") or "").strip().lower()
    tavily = (get("TAVILY_API_KEY") or "").strip()
    brave = (get("BRAVE_SEARCH_API_KEY") or "").strip()

    if forced:
        if forced == "tavily":
            if not tavily:
                raise WebToolError(
                    "[web_search] SAFECLAW_WEB_SEARCH_PROVIDER=tavily but TAVILY_API_KEY is empty\n"
                    "  Set TAVILY_API_KEY or unset SAFECLAW_WEB_SEARCH_PROVIDER"
                )
            return "tavily", tavily
        if forced == "brave":
            if not brave:
                raise WebToolError(
                    "[web_search] SAFECLAW_WEB_SEARCH_PROVIDER=brave but BRAVE_SEARCH_API_KEY is empty\n"
                    "  Set BRAVE_SEARCH_API_KEY or unset SAFECLAW_WEB_SEARCH_PROVIDER"
                )
            return "brave", brave
        if forced in {"ddg", "duckduckgo", "instant"}:
            return "duckduckgo", None
        raise WebToolError(
            "[web_search] Unknown SAFECLAW_WEB_SEARCH_PROVIDER\n"
            "  Expected: tavily | brave | duckduckgo\n"
            f"  Actual: {forced!r}"
        )

    if tavily:
        return "tavily", tavily
    if brave:
        return "brave", brave
    return "duckduckgo", None


def search_web(
    query: str,
    *,
    max_results: int = DEFAULT_SEARCH_MAX_RESULTS,
    client: Optional[httpx.Client] = None,
    env: Optional[Callable[[str], Optional[str]]] = None,
) -> str:
    """Search the web; returns a formatted result block for the agent."""
    q = (query or "").strip()
    if not q:
        raise WebToolError(
            "[web_search] query is required\n"
            "  Actual: empty/whitespace"
        )
    limit = max(1, min(int(max_results or DEFAULT_SEARCH_MAX_RESULTS), 10))
    provider, api_key = resolve_search_provider(env)

    owns = client is None
    http = client or _client_factory()
    try:
        try:
            if provider == "tavily":
                assert api_key is not None
                items = _search_tavily(q, limit, http, api_key)
            elif provider == "brave":
                assert api_key is not None
                items = _search_brave(q, limit, http, api_key)
            else:
                items = _search_duckduckgo_ia(q, limit, http)
        except httpx.HTTPError as exc:
            raise WebToolError(
                f"[web_search] Request failed\n"
                f"  Provider: {provider}\n"
                f"  Query: {q}\n"
                f"  Error: {type(exc).__name__}: {exc}"
            ) from exc
    finally:
        if owns:
            http.close()

    items = [i for i in items if (i.get("title") or i.get("url") or i.get("snippet"))]
    if not items:
        raise WebToolError(
            "[web_search] No useful results\n"
            f"  Provider: {provider}\n"
            f"  Query: {q}\n"
            "  Hint: DuckDuckGo Instant Answer is not a full SERP. "
            "Set TAVILY_API_KEY or BRAVE_SEARCH_API_KEY for organic results, "
            "or try web_fetch on a known URL."
        )
    logger.info("[web_search] provider=%s query=%r hits=%d", provider, q, len(items))
    return _format_results(q, provider, items[:limit])
