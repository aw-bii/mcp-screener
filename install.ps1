$Repo = "https://github.com/aw-bii/mcp-screener.git"

Write-Host "==> Installing screener-mcp from $Repo" -ForegroundColor Green
pip install $Repo

Write-Host ""
Write-Host "==> Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To configure Claude Desktop, add this to your claude_desktop_config.json:"
Write-Host ""
@'
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
'@
Write-Host ""
Write-Host "Get your session ID from screener.in browser cookies (sessionid)."
Write-Host "Run 'screener-mcp' to start the server."
