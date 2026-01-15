"""Tests for metadata scraping functionality."""

import pytest
from bib_enrich_mcp.scrapers import (
    MetadataResult,
    ArxivScraper,
    DBLPScraper,
    CrossRefScraper,
    scrape_metadata,
)


class TestMetadataResult:
    """Tests for MetadataResult dataclass."""

    def test_create_result(self):
        """Test creating a MetadataResult."""
        result = MetadataResult(
            title="Test Paper",
            authors=["John Doe"],
            year="2024",
            source="arxiv",
        )
        assert result.title == "Test Paper"
        assert result.source == "arxiv"

    def test_result_with_all_fields(self):
        """Test MetadataResult with all optional fields."""
        result = MetadataResult(
            title="Full Paper",
            authors=["Jane Doe", "John Smith"],
            year="2024",
            venue="NeurIPS",
            doi="10.1234/test",
            arxiv_id="2401.12345",
            booktitle="NeurIPS 2024",
            journal=None,
            volume="37",
            pages="1-10",
            publisher="NeurIPS Foundation",
            source="dblp",
            confidence=0.95,
        )
        assert result.confidence == 0.95
        assert result.venue == "NeurIPS"


class TestArxivScraper:
    """Tests for ArXiv metadata scraper."""

    @pytest.fixture
    def scraper(self):
        return ArxivScraper()

    @pytest.mark.asyncio
    async def test_search_by_arxiv_id(self, scraper, httpx_mock):
        """Test searching by arXiv ID."""
        httpx_mock.add_response(
            url="https://export.arxiv.org/api/query?id_list=2401.12345",
            text="""<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry>
                    <title>Test Paper Title</title>
                    <author><name>John Doe</name></author>
                    <author><name>Jane Smith</name></author>
                    <published>2024-01-15T00:00:00Z</published>
                    <id>http://arxiv.org/abs/2401.12345v1</id>
                </entry>
            </feed>""",
        )
        result = await scraper.search_by_arxiv_id("2401.12345")
        assert result is not None
        assert result.title == "Test Paper Title"
        assert result.arxiv_id == "2401.12345"

    @pytest.mark.asyncio
    async def test_search_by_title(self, scraper, httpx_mock):
        """Test searching by title."""
        httpx_mock.add_response(
            text="""<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry>
                    <title>Attention Is All You Need</title>
                    <author><name>Ashish Vaswani</name></author>
                    <published>2017-06-12T00:00:00Z</published>
                    <id>http://arxiv.org/abs/1706.03762v1</id>
                </entry>
            </feed>"""
        )
        result = await scraper.search_by_title("Attention Is All You Need")
        assert result is not None
        assert "Attention" in result.title

    @pytest.mark.asyncio
    async def test_search_not_found(self, scraper, httpx_mock):
        """Test search returns None when not found."""
        httpx_mock.add_response(
            text="""<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
            </feed>"""
        )
        result = await scraper.search_by_arxiv_id("9999.99999")
        assert result is None


class TestDBLPScraper:
    """Tests for DBLP metadata scraper."""

    @pytest.fixture
    def scraper(self):
        return DBLPScraper()

    @pytest.mark.asyncio
    async def test_search_by_title(self, scraper, httpx_mock):
        """Test searching DBLP by title."""
        httpx_mock.add_response(
            json={
                "result": {
                    "hits": {
                        "hit": [
                            {
                                "info": {
                                    "title": "Attention Is All You Need",
                                    "authors": {
                                        "author": [
                                            {"text": "Ashish Vaswani"},
                                            {"text": "Noam Shazeer"},
                                        ]
                                    },
                                    "year": "2017",
                                    "venue": "NIPS",
                                    "doi": "10.5555/3295222.3295349",
                                }
                            }
                        ]
                    }
                }
            }
        )
        result = await scraper.search_by_title("Attention Is All You Need")
        assert result is not None
        assert "Attention" in result.title

    @pytest.mark.asyncio
    async def test_search_not_found(self, scraper, httpx_mock):
        """Test DBLP search returns None when not found."""
        httpx_mock.add_response(json={"result": {"hits": {"hit": []}}})
        result = await scraper.search_by_title("Nonexistent Paper XYZ123")
        assert result is None


class TestCrossRefScraper:
    """Tests for CrossRef metadata scraper."""

    @pytest.fixture
    def scraper(self):
        return CrossRefScraper()

    @pytest.mark.asyncio
    async def test_search_by_doi(self, scraper, httpx_mock):
        """Test searching CrossRef by DOI."""
        httpx_mock.add_response(
            json={
                "status": "ok",
                "message": {
                    "title": ["Test Paper"],
                    "author": [{"given": "John", "family": "Doe"}],
                    "published-print": {"date-parts": [[2024]]},
                    "DOI": "10.1234/test",
                    "container-title": ["Nature"],
                    "volume": "123",
                    "page": "1-10",
                },
            }
        )
        result = await scraper.search_by_doi("10.1234/test")
        assert result is not None
        assert result.doi == "10.1234/test"

    @pytest.mark.asyncio
    async def test_search_by_title(self, scraper, httpx_mock):
        """Test searching CrossRef by title."""
        httpx_mock.add_response(
            json={
                "status": "ok",
                "message": {
                    "items": [
                        {
                            "title": ["Attention Is All You Need"],
                            "author": [{"given": "Ashish", "family": "Vaswani"}],
                            "published-print": {"date-parts": [[2017]]},
                            "DOI": "10.5555/3295222.3295349",
                        }
                    ]
                },
            }
        )
        result = await scraper.search_by_title("Attention Is All You Need")
        assert result is not None


class TestScrapeMetadata:
    """Tests for the main scrape_metadata function."""

    @pytest.mark.asyncio
    async def test_scrape_with_arxiv_id(self, httpx_mock):
        """Test scraping with arXiv ID."""
        httpx_mock.add_response(
            text="""<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry>
                    <title>Test Paper</title>
                    <author><name>John Doe</name></author>
                    <published>2024-01-15T00:00:00Z</published>
                    <id>http://arxiv.org/abs/2401.12345v1</id>
                </entry>
            </feed>"""
        )
        results = await scrape_metadata(arxiv_id="2401.12345")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_scrape_with_title(self, httpx_mock):
        """Test scraping with title only."""
        # Mock responses for all scrapers
        httpx_mock.add_response(
            text="""<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
            </feed>"""
        )
        httpx_mock.add_response(json={"result": {"hits": {"hit": []}}})
        httpx_mock.add_response(json={"status": "ok", "message": {"items": []}})

        results = await scrape_metadata(title="Some Paper Title")
        assert isinstance(results, list)
