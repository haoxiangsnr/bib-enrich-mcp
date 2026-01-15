"""Tests for MCP server functionality."""

import pytest
from bib_enrich_mcp.server import enrich_bib_entry, enrich_bib_file


class TestEnrichBibEntry:
    """Tests for the enrich_bib_entry tool."""

    @pytest.mark.asyncio
    async def test_enrich_with_arxiv_id(self, httpx_mock):
        """Test enriching entry with arXiv ID."""
        httpx_mock.add_response(
            text="""<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry>
                    <title>Test Paper Title</title>
                    <author><name>John Doe</name></author>
                    <published>2024-01-15T00:00:00Z</published>
                    <id>http://arxiv.org/abs/2401.12345v1</id>
                </entry>
            </feed>"""
        )
        result = await enrich_bib_entry(cite_key="test2024", arxiv_id="2401.12345")
        assert "Test Paper Title" in result
        assert "2024" in result

    @pytest.mark.asyncio
    async def test_enrich_with_title(self, httpx_mock):
        """Test enriching entry with title search."""
        httpx_mock.add_response(
            text="""<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
            </feed>"""
        )
        httpx_mock.add_response(json={"result": {"hits": {"hit": []}}})
        httpx_mock.add_response(json={"status": "ok", "message": {"items": []}})
        result = await enrich_bib_entry(cite_key="test2024", title="Some Paper")
        assert isinstance(result, str)


class TestEnrichBibFile:
    """Tests for the enrich_bib_file tool."""

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_enrich_file(self, tmp_path, httpx_mock):
        """Test enriching a bib file."""
        import re

        bib_content = """
        @misc{test2024,
            title = {Test Paper},
            eprint = {2401.12345},
        }
        """
        bib_file = tmp_path / "test.bib"
        bib_file.write_text(bib_content)

        # Mock all arxiv requests
        httpx_mock.add_response(
            url=re.compile(r"https://export\.arxiv\.org/.*"),
            text="""<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry>
                    <title>Test Paper Title</title>
                    <author><name>John Doe</name></author>
                    <published>2024-01-15T00:00:00Z</published>
                    <id>http://arxiv.org/abs/2401.12345v1</id>
                </entry>
            </feed>""",
        )
        # Mock DBLP search
        httpx_mock.add_response(
            url=re.compile(r"https://dblp\.org/.*"),
            json={"result": {"hits": {"hit": []}}},
        )
        # Mock CrossRef search
        httpx_mock.add_response(
            url=re.compile(r"https://api\.crossref\.org/.*"),
            json={"status": "ok", "message": {"items": []}},
        )

        result = await enrich_bib_file(str(bib_file))
        assert "enriched" in result.lower() or "1" in result
