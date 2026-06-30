#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/aw-bii/mcp-screener.git"

echo "==> Installing screener-mcp from $REPO"
pip install "$REPO" 2>/dev/null || pip3 install "$REPO"

echo ""
echo "==> Setup complete!"
echo ""
echo "To configure Claude Desktop, add this to your claude_desktop_config.json:"
echo ""
cat <<'CONFIG'
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
CONFIG
echo ""
echo "Get your session ID from screener.in browser cookies (sessionid)."
echo "Run 'screener-mcp' to start the server."
