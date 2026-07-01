from __future__ import annotations
import time
import httpx
from bs4 import BeautifulSoup


class ScreenerClient:
    BASE_URL = "https://www.screener.in"

    def __init__(self, session_id: str | None = None):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.client = httpx.Client(headers=headers, follow_redirects=True, timeout=30)
        if session_id:
            self.client.cookies.set("sessionid", session_id)
        self._last_request = 0.0

    def _rate_limit(self):
        elapsed = time.time() - self._last_request
        if elapsed < 1.5:
            time.sleep(1.5 - elapsed)

    def _fetch(self, url: str) -> str:
        self._rate_limit()
        for attempt in range(3):
            try:
                resp = self.client.get(url)
                if resp.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                self._last_request = time.time()
                return resp.text
            except httpx.HTTPStatusError:
                raise
        raise RuntimeError(f"Rate limited after 3 retries: {url}")

    def _soup(self, url: str) -> BeautifulSoup:
        return BeautifulSoup(self._fetch(url), "lxml")


    def _parse_table(self, soup: BeautifulSoup, section_id: str) -> list[dict]:
        section = soup.find("section", id=section_id)
        if not section:
            return []
        table = section.find("table")
        if not table:
            return []
        thead = table.find("thead")
        tbody = table.find("tbody")
        if not thead or not tbody:
            return []
        headers = [th.get_text(strip=True) for th in thead.find_all("th")]
        rows = []
        for tr in tbody.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells:
                rows.append(dict(zip(headers, cells)))
        return rows

    def get_company_info(self, symbol: str) -> dict:
        soup = self._soup(f"{self.BASE_URL}/company/{symbol}/")
        info = {}
        company_name = soup.find("h1", class_="h2")
        if company_name:
            info["name"] = company_name.get_text(strip=True)
        company_links = soup.find("div", class_="company-links")
        if company_links:
            links = company_links.find_all("a")
            if links:
                info["website"] = links[0].get_text(strip=True)
            for span in company_links.find_all("span"):
                text = span.get_text(" ", strip=True)
                if text.startswith("BSE:"):
                    info["bse_code"] = text.replace("BSE:", "").strip()
                elif text.startswith("NSE:"):
                    info["nse_symbol"] = text.replace("NSE:", "").strip()
        for li in soup.select("#top-ratios li"):
            name_el = li.find("span", class_="name")
            val_el = li.find("span", class_="number")
            if name_el and val_el:
                key = name_el.get_text(strip=True).lower().replace("/", "_").replace(" ", "_")
                info[key] = val_el.get_text(strip=True)
        peer_section = soup.find("section", id="peers")
        if peer_section:
            for a in peer_section.find_all("a", href=lambda h: h and "/market/" in h):
                title = a.get("title", "")
                if title:
                    key = title.lower().replace(" ", "_")
                    info.setdefault(key, a.get_text(strip=True))
        return info

    def get_trading_multiples(self, symbol: str) -> dict:
        soup = self._soup(f"{self.BASE_URL}/company/{symbol}/")
        multiples = {}
        for li in soup.select("#top-ratios li"):
            name_el = li.find("span", class_="name")
            if not name_el:
                continue
            key = name_el.get_text(strip=True)
            # Collect all number spans — High/Low has two
            numbers = [s.get_text(strip=True) for s in li.find_all("span", class_="number")]
            if len(numbers) >= 2:
                multiples[key] = " / ".join(numbers)
            elif numbers:
                multiples[key] = numbers[0]
        # Calculate P/B if we have both price and book value
        try:
            price = float(multiples.get("Current Price", "0").replace(",", "") or 0)
            book = float(multiples.get("Book Value", "0").replace(",", "") or 0)
            if price and book:
                multiples["P/B"] = f"{price / book:.2f}"
        except (ValueError, ZeroDivisionError):
            pass
        return multiples

    def get_ratios(self, symbol: str) -> list[dict]:
        soup = self._soup(f"{self.BASE_URL}/company/{symbol}/")
        return self._parse_table(soup, "ratios")

    def get_shareholding(self, symbol: str) -> list[dict]:
        soup = self._soup(f"{self.BASE_URL}/company/{symbol}/")
        return self._parse_table(soup, "shareholding")

    def get_financials(self, symbol: str) -> dict:
        soup = self._soup(f"{self.BASE_URL}/company/{symbol}/")
        return {
            "profit_loss": self._parse_table(soup, "profit-loss"),
            "balance_sheet": self._parse_table(soup, "balance-sheet"),
            "cash_flow": self._parse_table(soup, "cash-flow"),
        }

    def get_quarterly_results(self, symbol: str) -> list[dict]:
        soup = self._soup(f"{self.BASE_URL}/company/{symbol}/")
        return self._parse_table(soup, "quarters")

    def get_sectors(self) -> list[str]:
        soup = self._soup(f"{self.BASE_URL}/screens/")
        return list(dict.fromkeys(
            a.get_text(strip=True)
            for a in soup.select("a[href*='/sector/']")
            if a.get_text(strip=True)
        ))

    def get_peers(self, symbol: str) -> list[dict]:
        soup = self._soup(f"{self.BASE_URL}/company/{symbol}/")
        peer_section = soup.find("section", id="peers")
        if not peer_section:
            return []
        # Peer table is JS-rendered; use the industry market page instead.
        # Prefer the most specific classification level available.
        industry_link = (
            peer_section.find("a", title="Industry")
            or peer_section.find("a", title="Broad Industry")
            or peer_section.find("a", title="Sector")
        )
        if not industry_link:
            return []
        market_soup = self._soup(self.BASE_URL + industry_link["href"])
        table = market_soup.find("table")
        if not table:
            return []
        trs = table.find_all("tr")
        if not trs:
            return []
        headers = [c.get_text(strip=True) for c in trs[0].find_all(["th", "td"])]
        rows = []
        for tr in trs[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells:
                rows.append(dict(zip(headers, cells)))
        return rows

