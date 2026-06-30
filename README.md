# screener-mcp

MCP server for [Screener.in](https://www.screener.in/) financial data — Indian stock market fundamentals, ratios, quarterly results, shareholding, and stock screening.

## One-Command Install

### macOS/Linux

```bash
curl -fsSL https://raw.githubusercontent.com/aw-bii/mcp-screener/main/install.sh | sh
```

### Windows (PowerShell)

```powershell
powershell -c "irm https://raw.githubusercontent.com/aw-bii/mcp-screener/main/install.ps1 | iex"
```

### Manual (any platform)

```bash
pip install git+https://github.com/aw-bii/mcp-screener.git
```

## Configuration

1. Get your `sessionid` cookie from [screener.in](https://www.screener.in/) (browser dev tools → Cookies)
2. Add to your MCP client config:

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

Without a session ID, company data tools work. Screen queries require authentication.

## Tools

| Tool | Description |
|------|-------------|
| `run_screen` | Run stock screening queries |
| `get_company_info` | Company profile, BSE/NSE codes |
| `get_financials` | P&L, balance sheet, cash flow |
| `get_quarterly_results` | Quarterly sales/profit/margins |
| `get_trading_multiples` | P/E, P/B, EV/EBITDA, market cap, dividend yield |
| `get_ratios` | ROCE, ROE, D/E, current ratio, etc. |
| `get_shareholding` | Promoter, FII, DII trends |
| `get_peers` | Sector & industry classification |

## Development

```bash
git clone https://github.com/aw-bii/mcp-screener.git
cd mcp-screener
pip install -e .
screener-mcp
```
