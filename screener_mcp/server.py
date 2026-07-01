from __future__ import annotations
import json
import os
from collections.abc import Iterable
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.lowlevel.server import ReadResourceContents
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, ResourceTemplate, ServerCapabilities, Tool, TextContent
from pydantic import AnyUrl
from .client import ScreenerClient

load_dotenv()

client = ScreenerClient(session_id=os.getenv("SCREENER_SESSION_ID"))

server = Server("screener-mcp")


def _err(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error: {msg}")]


def _ok(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="run_screen",
            description="Run a Screener.in stock screening query. Example: 'Market capitalization > 500 AND Price to earning < 15'. Default columns returned: S.No., Name, CMP, P/E, Mar Cap Cr., Div Yld %, NP Qtr Cr., Qtr Profit Var %, Sales Qtr Cr., Qtr Sales Var %, ROCE %. Pass columns to filter to a subset using these names (or common aliases like 'Market Cap', 'Price', 'Dividend Yield').",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Screener.in query string"},
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional column names to include (default: all columns)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_company_info",
            description="Get basic company profile: name, website, sector/industry, BSE/NSE codes, market cap, current price, 52-week high/low, P/E, book value, dividend yield",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Company symbol (e.g. INFY, RELIANCE)"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_financials",
            description="Get P&L, balance sheet, and cash flow data for a company",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Company symbol"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_quarterly_results",
            description="Get quarterly results for a company",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Company symbol"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_trading_multiples",
            description="Get valuation metrics: Market Cap, Current Price, 52-week High/Low, P/E, Book Value, P/B (calculated), Dividend Yield, ROCE, ROE",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Company symbol"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_ratios",
            description="Get profitability and health ratios: ROCE, ROE, OPM, NPM, D/E, current ratio, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Company symbol"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_shareholding",
            description="Get shareholding pattern: promoter, FII, DII, public holding trends",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Company symbol"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_peers",
            description="Get peer comparison table for a company — all companies in the same industry with CMP, P/E, Market Cap, Dividend Yield, quarterly financials and ROCE",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Company symbol"}
                },
                "required": ["symbol"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        match name:
            case "run_screen":
                return _ok(client.run_screen(arguments["query"], arguments.get("columns")))
            case "get_company_info":
                return _ok(client.get_company_info(arguments["symbol"]))
            case "get_financials":
                return _ok(client.get_financials(arguments["symbol"]))
            case "get_quarterly_results":
                return _ok(client.get_quarterly_results(arguments["symbol"]))
            case "get_trading_multiples":
                return _ok(client.get_trading_multiples(arguments["symbol"]))
            case "get_ratios":
                return _ok(client.get_ratios(arguments["symbol"]))
            case "get_shareholding":
                return _ok(client.get_shareholding(arguments["symbol"]))
            case "get_peers":
                return _ok(client.get_peers(arguments["symbol"]))
            case _:
                return _err(f"Unknown tool: {name}")
    except Exception as e:
        return _err(str(e))


@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(uri=AnyUrl("screener://sectors"), name="Available Sectors", description="List of all market sectors on Screener.in"),
    ]


@server.list_resource_templates()
async def list_resource_templates() -> list[ResourceTemplate]:
    return [
        ResourceTemplate(
            name="Company Snapshot",
            uriTemplate="screener://company/{symbol}",
            description="Combined snapshot: info, multiples, ratios, quarterly, shareholding for a company. Replace {symbol} with company symbol (e.g. INFY, RELIANCE).",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: AnyUrl) -> Iterable[ReadResourceContents]:
    uri_str = str(uri)
    if uri_str == "screener://sectors":
        sectors = client.get_sectors()
        content = json.dumps(sectors, indent=2) if sectors else "No sectors found. Set SCREENER_SESSION_ID in .env for full access."
        return [ReadResourceContents(
            content=content,
            mime_type="application/json" if sectors else "text/plain",
        )]
    if uri_str.startswith("screener://company/"):
        symbol = uri_str.split("/")[-1]
        data = {
            "info": client.get_company_info(symbol),
            "multiples": client.get_trading_multiples(symbol),
            "ratios": client.get_ratios(symbol),
            "quarterly": client.get_quarterly_results(symbol),
            "shareholding": client.get_shareholding(symbol),
        }
        return [ReadResourceContents(
            content=json.dumps(data, indent=2, default=str),
            mime_type="application/json",
        )]
    return [ReadResourceContents(
        content=f"Error: Unknown resource: {uri}",
        mime_type="text/plain",
    )]


async def main():
    options = InitializationOptions(
        server_name="screener-mcp",
        server_version="0.1.0",
        capabilities=ServerCapabilities(),
    )
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], options)


def run():
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    run()
