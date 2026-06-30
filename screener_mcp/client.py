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

    def _ensure_csrf(self):
        if not self.client.cookies.get("csrftoken"):
            self._fetch("https://www.screener.in/")

    def _get_screen(self, query: str) -> str:
        self._ensure_csrf()
        for attempt in range(3):
            try:
                resp = self.client.get(
                    f"{self.BASE_URL}/screen/raw/",
                    params={"query": query},
                )
                if resp.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                self._last_request = time.time()
                return resp.text
            except httpx.HTTPStatusError:
                raise
        raise RuntimeError(f"Rate limited after 3 retries for query: {query}")

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
            if cells and len(cells) == len(headers):
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
        ratio_section = soup.find("div", class_="company-ratios")
        if ratio_section:
            for li in ratio_section.find_all("li"):
                name_span = li.find("span", class_="name")
                if name_span:
                    key = name_span.get_text(strip=True).lower().replace(" ", "_")
                    spans = li.find_all("span")
                    if len(spans) >= 3:
                        multiples[key] = spans[-1].get_text(strip=True)
                    elif len(spans) >= 2:
                        multiples[key] = spans[1].get_text(strip=True)
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
        table = peer_section.find("table")
        if table:
            thead = table.find("thead")
            tbody = table.find("tbody")
            if thead and tbody:
                headers = [th.get_text(strip=True) for th in thead.find_all("th")]
                rows = []
                for tr in tbody.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if cells:
                        rows.append(dict(zip(headers, cells)))
                if rows:
                    return rows
        # Fallback: extract company links from the peers section
        companies = []
        for a in peer_section.find_all("a", href=lambda h: h and "/company/" in h):
            name = a.get_text(strip=True)
            slug = a["href"].strip("/").split("/")[-1]
            if name and slug:
                companies.append({"name": name, "symbol": slug})
        return companies

    def run_screen(self, query: str, columns: list[str] | None = None) -> list[dict]:
        effective_query = query
        if columns and "select" not in query.lower():
            effective_query = f"{query} select {', '.join(columns)}"
        html = self._get_screen(effective_query)
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table", class_="data-table")
        if not table:
            return []
        rows = table.find_all("tr")
        if not rows:
            return []
        header_row = rows[0]
        headers = []
        for th in header_row.find_all("th"):
            parts = [s for s in th.stripped_strings if s != "Rs."]
            headers.append(" ".join(parts) if len(parts) > 1 else parts[0] if parts else "")
        data_rows = []
        for tr in rows[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if not cells:
                continue
            row = {}
            for i, h in enumerate(headers):
                if i < len(cells):
                    row[h] = cells[i]
            data_rows.append(row)
        return data_rows
