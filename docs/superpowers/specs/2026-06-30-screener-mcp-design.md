# Screener.in MCP Server — Design Spec

## Overview

An MCP server that exposes Screener.in financial data (Indian stock market) as composable tools and resources. Built in Python using `mcp`, `httpx`, and `BeautifulSoup`.

## Architecture

Single-file structure:

```
screener-mcp/
├── server.py              # MCP server entry point, tool/resource definitions
├── screener_client.py     # httpx client, HTML parsing, data extraction
├── requirements.txt       # mcp, httpx, beautifulsoup4, lxml, python-dotenv
└── .env                   # SCREENER_SESSION_ID (optional, for authenticated access)
```

## Authentication

Optional — configure via `.env`:

```
SCREENER_SESSION_ID=sessionid_value
```

If set, the session cookie is injected into all requests, enabling access to:
- Saved screens
- Custom ratios
- Premium features (if the session belongs to a premium account)

Without auth, all public company pages and basic screen queries still work.

## Approach

**Strategy:** Pure HTML scraper via `httpx` + `BeautifulSoup`.
- Screener.in pages are server-rendered HTML — no JS required for core data.
- CSS selectors target known section IDs (`#profit-loss`, `#balance-sheet`, `#ratios`, `#quarters`, `#shareholding`).
- Screen queries: POST to `/screen/new/` with query string, parse result table.
- Rate limiting: 1 request per 1.5s, 2 retries on 429.

## MCP Tools

### `run_screen(query, columns=None)`
- **Input:** Screener.in query string (e.g. `"Market capitalization > 500 AND Price to earning < 15"`), optional columns list
- **Output:** List of dicts — each row from the results table
- **Default columns:** S.No., Name, CMP, P/E, Mar Cap, Div Yld, NP Qtr, Qtr Profit Var %, Sales Qtr, Qtr Sales Var %, ROCE %

### `get_company_info(symbol)`
- **Input:** Company symbol (e.g. `INFY`, `RELIANCE`)
- **Output:** Profile dict — name, sector, industry, market cap, CMP, 52-week high/low, face value, book value

### `get_financials(symbol)`
- **Input:** Company symbol
- **Output:** Dict with `profit_loss` (list of year rows), `balance_sheet` (list), `cash_flow` (list)

### `get_quarterly_results(symbol)`
- **Input:** Company symbol
- **Output:** List of recent quarters with sales, net profit, margins, YoY/QoQ variance

### `get_trading_multiples(symbol)`
- **Input:** Company symbol
- **Output:** Dict — P/E, P/B, P/S, EV/EBITDA, EV/Sales, Enterprise Value, Market Cap, Dividend Yield, Price/Book

### `get_ratios(symbol)`
- **Input:** Company symbol
- **Output:** Dict — ROCE, ROE, OPM, NPM, Debt/Equity, Current Ratio, Interest Coverage, Inventory Turnover, Days Receivable, Asset Turnover

### `get_shareholding(symbol)`
- **Input:** Company symbol
- **Output:** List of quarters with promoter %, FII %, DII %, public %, pledge %

### `get_peers(symbol)`
- **Input:** Company symbol
- **Output:** List of peer companies with comparative metrics (CMP, P/E, Mkt Cap, ROCE, growth)

## MCP Resources

- `screener://company/{symbol}` — structured JSON snapshot combining info, multiples, ratios, quarterly, shareholding
- `screener://sectors` — list of available sectors

## Error Handling

- HTTP errors → descriptive `MCPError` messages
- Parsing failures → fallback to raw table extraction
- Auth failures → clear message to set session ID
- Rate limit (429) → automatic retry with backoff

## Testing

- Manual testing via MCP Inspector or Claude Desktop during development
- Unit tests for parsers with cached HTML fixtures

## Future Considerations

- Custom ratio support (post-MVP)
- CSV export for screen results
- Watchlist management
- Screener AI integration
