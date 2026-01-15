"""Metadata scrapers for academic papers."""

from dataclasses import dataclass
import re
import httpx
from bs4 import BeautifulSoup


@dataclass
class MetadataResult:
    """Result from a metadata scraper."""

    title: str
    authors: list[str] | None = None
    year: str | None = None
    venue: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    booktitle: str | None = None
    journal: str | None = None
    volume: str | None = None
    pages: str | None = None
    publisher: str | None = None
    source: str = ""
    confidence: float = 0.0


class ArxivScraper:
    """Scraper for arXiv metadata."""

    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def search_by_arxiv_id(self, arxiv_id: str) -> MetadataResult | None:
        """Search arXiv by ID."""
        client = await self._get_client()
        url = f"{self.BASE_URL}?id_list={arxiv_id}"
        response = await client.get(url)
        return self._parse_response(response.text, arxiv_id)

    async def search_by_title(self, title: str) -> MetadataResult | None:
        """Search arXiv by title."""
        client = await self._get_client()
        query = f"ti:{title}"
        url = f"{self.BASE_URL}?search_query={query}&max_results=1"
        response = await client.get(url)
        return self._parse_response(response.text)

    def _parse_response(
        self, xml_text: str, arxiv_id: str | None = None
    ) -> MetadataResult | None:
        """Parse arXiv API XML response."""
        soup = BeautifulSoup(xml_text, "lxml-xml")
        entry = soup.find("entry")
        if not entry:
            return None

        title_elem = entry.find("title")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        authors = [
            a.find("name").get_text(strip=True)
            for a in entry.find_all("author")
            if a.find("name")
        ]

        published = entry.find("published")
        year = None
        if published:
            year = published.get_text(strip=True)[:4]

        # Extract arxiv_id from entry id if not provided
        if not arxiv_id:
            id_elem = entry.find("id")
            if id_elem:
                id_text = id_elem.get_text(strip=True)
                match = re.search(r"(\d+\.\d+)", id_text)
                if match:
                    arxiv_id = match.group(1)

        return MetadataResult(
            title=title,
            authors=authors if authors else None,
            year=year,
            arxiv_id=arxiv_id,
            source="arxiv",
            confidence=0.9,
        )


class DBLPScraper:
    """Scraper for DBLP metadata."""

    BASE_URL = "https://dblp.org/search/publ/api"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def search_by_title(self, title: str) -> MetadataResult | None:
        """Search DBLP by title."""
        client = await self._get_client()
        params = {"q": title, "format": "json", "h": 1}
        response = await client.get(self.BASE_URL, params=params)
        return self._parse_response(response.json())

    def _parse_response(self, data: dict) -> MetadataResult | None:
        """Parse DBLP API JSON response."""
        try:
            result = data.get("result")
            if not result:
                return None
            hits = result.get("hits", {}).get("hit", [])
            if not hits:
                return None

            info = hits[0].get("info", {})
            title = info.get("title", "")
            if not title:
                return None

            authors = self._extract_authors(info)
            year = info.get("year")
            venue = info.get("venue")
            doi = info.get("doi")

            return MetadataResult(
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                doi=doi,
                source="dblp",
                confidence=0.85,
            )
        except (KeyError, IndexError):
            return None

    def _extract_authors(self, info: dict) -> list[str] | None:
        """Extract authors from DBLP info."""
        authors_data = info.get("authors", {}).get("author", [])
        if isinstance(authors_data, dict):
            authors_data = [authors_data]
        authors = []
        for a in authors_data:
            if isinstance(a, dict):
                authors.append(a.get("text", ""))
            elif isinstance(a, str):
                authors.append(a)
        return authors if authors else None


class CrossRefScraper:
    """Scraper for CrossRef metadata."""

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def search_by_doi(self, doi: str) -> MetadataResult | None:
        """Search CrossRef by DOI."""
        client = await self._get_client()
        url = f"{self.BASE_URL}/{doi}"
        response = await client.get(url)
        data = response.json()
        if data.get("status") != "ok":
            return None
        return self._parse_work(data.get("message", {}))

    async def search_by_title(self, title: str) -> MetadataResult | None:
        """Search CrossRef by title."""
        client = await self._get_client()
        params = {"query.title": title, "rows": 1}
        response = await client.get(self.BASE_URL, params=params)
        data = response.json()
        items = data.get("message", {}).get("items", [])
        if not items:
            return None
        return self._parse_work(items[0])

    def _parse_work(self, work: dict) -> MetadataResult | None:
        """Parse CrossRef work item."""
        title_list = work.get("title", [])
        title = title_list[0] if title_list else ""
        if not title:
            return None

        authors = self._extract_authors(work)
        year = self._extract_year(work)
        doi = work.get("DOI")
        journal_list = work.get("container-title", [])
        journal = journal_list[0] if journal_list else None
        volume = work.get("volume")
        pages = work.get("page")

        return MetadataResult(
            title=title,
            authors=authors,
            year=year,
            doi=doi,
            journal=journal,
            volume=volume,
            pages=pages,
            source="crossref",
            confidence=0.8,
        )

    def _extract_authors(self, work: dict) -> list[str] | None:
        """Extract authors from CrossRef work."""
        authors_data = work.get("author", [])
        authors = []
        for a in authors_data:
            given = a.get("given", "")
            family = a.get("family", "")
            name = f"{given} {family}".strip()
            if name:
                authors.append(name)
        return authors if authors else None

    def _extract_year(self, work: dict) -> str | None:
        """Extract year from CrossRef work."""
        for key in ["published-print", "published-online", "created"]:
            date_parts = work.get(key, {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                return str(date_parts[0][0])
        return None


async def scrape_metadata(
    title: str | None = None,
    arxiv_id: str | None = None,
    doi: str | None = None,
) -> list[MetadataResult]:
    """Scrape metadata from multiple sources."""
    results: list[MetadataResult] = []

    arxiv = ArxivScraper()
    dblp = DBLPScraper()
    crossref = CrossRefScraper()

    if arxiv_id:
        result = await arxiv.search_by_arxiv_id(arxiv_id)
        if result:
            results.append(result)

    if doi:
        result = await crossref.search_by_doi(doi)
        if result:
            results.append(result)

    if title:
        arxiv_result = await arxiv.search_by_title(title)
        if arxiv_result:
            results.append(arxiv_result)

        dblp_result = await dblp.search_by_title(title)
        if dblp_result:
            results.append(dblp_result)

        crossref_result = await crossref.search_by_title(title)
        if crossref_result:
            results.append(crossref_result)

    return results
