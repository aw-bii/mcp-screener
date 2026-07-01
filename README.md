# screener-mcp

MCP server for [Screener.in](https://www.screener.in/) financial data — Indian stock market fundamentals, ratios, quarterly results, shareholding, and peer comparison.

## Install

```bash
pip install git+https://github.com/aw-bii/mcp-screener.git
```

To update to the latest version:

```bash
pip install --force-reinstall git+https://github.com/aw-bii/mcp-screener.git
```

## Configuration

1. Log into [screener.in](https://www.screener.in/) in your browser
2. Open DevTools (F12) → Application → Cookies → `screener.in` → copy the `sessionid` value
3. Add to your MCP client config:

```json
{
  "mcpServers": {
    "screener-mcp": {
      "command": "screener-mcp",
      "env": {
        "SCREENER_SESSION_ID": "your_session_id_here"
      }
    }
  }
}
```

Without a session ID, all company data tools work. A session ID unlocks peer comparison data.

## Tools

| Tool | Description |
| --- | --- |
| `get_company_info` | Company profile, BSE/NSE codes, market cap, P/E, book value |
| `get_financials` | P&L, balance sheet, cash flow |
| `get_quarterly_results` | Quarterly sales/profit/margins |
| `get_trading_multiples` | Market Cap, CMP, High/Low, P/E, P/B, Dividend Yield, ROCE, ROE |
| `get_ratios` | ROCE, ROE, OPM, NPM, D/E, current ratio, etc. |
| `get_shareholding` | Promoter, FII, DII trends |
| `get_peers` | All companies in the same industry with key financials |

## Development

```bash
git clone https://github.com/aw-bii/mcp-screener.git
cd mcp-screener
pip install -e .
screener-mcp
```
