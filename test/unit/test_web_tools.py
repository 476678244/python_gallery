"""Unit tests for first-class web_fetch / web_search."""

from __future__ import annotations

import socket
from unittest.mock import MagicMock

import httpx
import pytest

from safe_claw.core.tools.manager import ToolManager
from safe_claw.core.tools.web import (
    WebToolError,
    fetch_url,
    resolve_search_provider,
    search_web,
    validate_public_http_url,
)


def _public_dns(host, *args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0))]


def test_validate_blocks_localhost():
    with pytest.raises(WebToolError, match="SSRF"):
        validate_public_http_url("http://localhost:8000/secret")


def test_validate_blocks_non_http():
    with pytest.raises(WebToolError, match="http/https"):
        validate_public_http_url("file:///etc/passwd")


def test_fetch_url_extracts_html(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith("https://example.com")
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<html><head><script>x()</script></head><body><h1>Hello</h1><p>World</p></body></html>",
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        out = fetch_url("https://example.com/page", client=client)
    assert "Status: 200" in out
    assert "Hello" in out and "World" in out
    assert "x()" not in out


def test_fetch_http_error_fail_fast(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="missing")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(WebToolError, match="HTTP error"):
            fetch_url("https://example.com/missing", client=client)


def test_search_tavily(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    env = {"TAVILY_API_KEY": "tvly-test", "BRAVE_SEARCH_API_KEY": ""}.get

    def handler(request: httpx.Request) -> httpx.Response:
        assert "tavily.com" in str(request.url)
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "SafeClaw docs",
                        "url": "https://example.com/docs",
                        "content": "Agent tools overview",
                    }
                ]
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        out = search_web("SafeClaw tools", max_results=3, client=client, env=env)
    assert "tavily" in out
    assert "SafeClaw docs" in out
    assert "https://example.com/docs" in out


def test_search_ddg_empty_fail_fast(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    env = {"TAVILY_API_KEY": "", "BRAVE_SEARCH_API_KEY": ""}.get

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"AbstractText": "", "RelatedTopics": [], "Answer": ""},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(WebToolError, match="No useful results"):
            search_web("zzzz-no-hit", client=client, env=env)


def test_resolve_provider_forced_tavily_missing_key():
    with pytest.raises(WebToolError, match="TAVILY_API_KEY"):
        resolve_search_provider(
            env={"SAFECLAW_WEB_SEARCH_PROVIDER": "tavily", "TAVILY_API_KEY": ""}.get
        )


def test_tool_manager_registers_web_tools():
    tm = ToolManager(
        skill_scanner=MagicMock(),
        skill_discovery=MagicMock(),
        skill_executor=MagicMock(),
    )
    names = {getattr(t, "name", "") for t in tm.get_builtin_tools()}
    assert "web_search" in names
    assert "web_fetch" in names


def test_web_search_tool_invokes(monkeypatch):
    monkeypatch.setattr(
        "safe_claw.core.tools.manager.search_web",
        lambda query, max_results=5: f"ok:{query}:{max_results}",
    )
    tm = ToolManager(
        skill_scanner=MagicMock(),
        skill_discovery=MagicMock(),
        skill_executor=MagicMock(),
    )
    tool = next(t for t in tm.get_builtin_tools() if t.name == "web_search")
    assert tool.invoke({"query": "hello", "max_results": 3}) == "ok:hello:3"
