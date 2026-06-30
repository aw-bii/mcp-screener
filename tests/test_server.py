from __future__ import annotations
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.types import TextContent


class TestServerEndpoints:
    """Unit tests for server functions."""

    def test_client_creates(self):
        from screener_mcp.client import ScreenerClient
        c = ScreenerClient()
        assert c is not None
        assert c.BASE_URL == "https://www.screener.in"

    def test_server_imports(self):
        from screener_mcp.server import server, client, _ok, _err
        assert server is not None
        assert client is not None

    def test_ok_returns_json(self):
        from screener_mcp.server import _ok
        result = _ok({"a": 1})
        assert len(result) == 1
        assert result[0].type == "text"
        parsed = json.loads(result[0].text)
        assert parsed == {"a": 1}

    def test_ok_returns_json_list(self):
        from screener_mcp.server import _ok
        result = _ok([{"a": 1}, {"b": 2}])
        parsed = json.loads(result[0].text)
        assert len(parsed) == 2

    def test_err_returns_error_format(self):
        from screener_mcp.server import _err
        result = _err("something broke")
        assert "Error: something broke" in result[0].text

    def test_list_tools(self):
        from screener_mcp.server import list_tools
        import asyncio
        tools = asyncio.run(list_tools())
        names = [t.name for t in tools]
        assert "run_screen" in names
        assert "get_company_info" in names
        assert "get_financials" in names
        assert "get_quarterly_results" in names
        assert "get_trading_multiples" in names
        assert "get_ratios" in names
        assert "get_shareholding" in names
        assert "get_peers" in names
        assert len(tools) == 8

    def test_list_resources(self):
        from screener_mcp.server import list_resources
        import asyncio
        resources = asyncio.run(list_resources())
        uris = [str(r.uri) for r in resources]
        assert "screener://sectors" in uris
        assert len(resources) == 1  # only concrete resources, not templates

    def test_list_resource_templates(self):
        from screener_mcp.server import list_resource_templates
        import asyncio
        templates = asyncio.run(list_resource_templates())
        uris = [t.uriTemplate for t in templates]
        assert "screener://company/{symbol}" in uris
        assert len(templates) == 1

    def test_call_tool_unknown(self):
        from screener_mcp.server import call_tool
        import asyncio
        result = asyncio.run(call_tool("nonexistent", {}))
        assert "Error: Unknown tool" in result[0].text
