from __future__ import annotations
import pytest
from screener_mcp.client import ScreenerClient


@pytest.fixture
def client():
    return ScreenerClient()


@pytest.mark.live
class TestScreenerClientLive:
    """Live tests against Screener.in (require network)."""

    def test_get_company_info_infy(self, client):
        info = client.get_company_info("INFY")
        assert info["name"] == "Infosys Ltd"
        assert info["bse_code"] == "500209"
        assert info["nse_symbol"] == "INFY"
        assert info["website"] == "infosys.com"
        assert "market_cap" in info
        assert "current_price" in info
        assert any("high" in k for k in info)

    def test_get_trading_multiples_infy(self, client):
        multiples = client.get_trading_multiples("INFY")
        assert "market_cap" in multiples
        assert "stock_p/e" in multiples or "stock_p_e" in multiples
        assert "current_price" in multiples

    def test_get_financials_infy(self, client):
        fins = client.get_financials("INFY")
        assert "profit_loss" in fins
        assert "balance_sheet" in fins
        assert "cash_flow" in fins
        assert len(fins["profit_loss"]) > 0
        assert len(fins["balance_sheet"]) > 0

    def test_get_quarterly_results_infy(self, client):
        quarters = client.get_quarterly_results("INFY")
        assert len(quarters) > 0

    def test_get_ratios_infy(self, client):
        ratios = client.get_ratios("INFY")
        assert len(ratios) > 0

    def test_get_shareholding_infy(self, client):
        holding = client.get_shareholding("INFY")
        assert len(holding) > 0

    def test_get_peers_infy(self, client):
        peers = client.get_peers("INFY")
        assert len(peers) > 0

    def test_run_screen_no_session(self, client):
        result = client.run_screen("Market capitalization > 500")
        assert result == []

    def test_get_company_info_reliance(self, client):
        info = client.get_company_info("RELIANCE")
        assert "name" in info
        assert info["nse_symbol"] == "RELIANCE"
        assert "market_cap" in info

    def test_get_company_info_tcs(self, client):
        info = client.get_company_info("TCS")
        assert "name" in info
        assert "market_cap" in info

    def test_get_sectors(self, client):
        sectors = client.get_sectors()
        assert isinstance(sectors, list)
