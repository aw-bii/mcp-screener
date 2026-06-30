from __future__ import annotations
import asyncio
import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
from .client import ScreenerClient

load_dotenv()

client = ScreenerClient(session_id=os.getenv("SCREENER_SESSION_ID"))

server = Server("screener-mcp")


def _err(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error: {msg}")]


def _ok(data) -> list[TextContent]:
    return [TextContent(type="text", text=str(data))]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="run_screen",
            description="Run a Screener.in stock screening query. Example: 'Market capitalization > 500 AND Price to earning < 15'",
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
            description="Get basic company profile: name, sector, market cap, CMP, 52-week high/low",
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
            description="Get trading multiples: P/E, P/B, P/S, EV/EBITDA, EV/Sales, market cap, dividend yield",
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
            description="Get peer comparison data for a company",
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
async def list_resources() -> list[dict]:
    return [
        {"uri": "screener://sectors", "name": "Available Sectors"},
        {"uri": "screener://company/{symbol}", "name": "Company Snapshot (replace {symbol} with company symbol)"},
    ]


@server.read_resource()
async def read_resource(uri: str) -> list[TextContent]:
    if uri == "screener://sectors":
        return _ok("Set SCREENER_SESSION_ID in .env to access sector list. Available via get_company_info for individual companies.")
    if uri.startswith("screener://company/"):
        symbol = uri.split("/")[-1]
        data = {
            "info": client.get_company_info(symbol),
            "multiples": client.get_trading_multiples(symbol),
            "ratios": client.get_ratios(symbol),
            "quarterly": client.get_quarterly_results(symbol),
            "shareholding": client.get_shareholding(symbol),
        }
        return _ok(data)
    return _err(f"Unknown resource: {uri}")


async def main():
    async with server.run(
        initialization_options=InitializationOptions(
            server_name="screener-mcp",
            server_version="0.1.0",
        ),
    ) as session:
        await session.consume_notification_stream()



def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
