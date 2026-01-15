"""MCP Server for fixing and enriching BibTeX bibliography metadata."""

from fastmcp import FastMCP

from .bib_parser import (
    BibEntry,
    parse_bib_file,
    entry_to_bibtex,
    write_bib_file,
)
from .scrapers import scrape_metadata, MetadataResult

mcp = FastMCP("bib-fix")


def _merge_metadata(entry: BibEntry, result: MetadataResult) -> BibEntry:
    """Merge scraped metadata into existing entry."""
    return BibEntry(
        entry_type=entry.entry_type,
        cite_key=entry.cite_key,
        title=result.title or entry.title,
        authors=result.authors or entry.authors,
        year=result.year or entry.year,
        venue=result.venue or entry.venue,
        doi=result.doi or entry.doi,
        arxiv_id=result.arxiv_id or entry.arxiv_id,
        url=entry.url,
        abstract=entry.abstract,
        booktitle=result.booktitle or entry.booktitle,
        journal=result.journal or entry.journal,
        volume=result.volume or entry.volume,
        pages=result.pages or entry.pages,
        publisher=result.publisher or entry.publisher,
        raw_fields=entry.raw_fields,
    )


async def enrich_bib_entry(
    cite_key: str,
    title: str | None = None,
    arxiv_id: str | None = None,
    doi: str | None = None,
) -> str:
    """Enrich a bibliography entry by scraping metadata."""
    results = await scrape_metadata(
        title=title,
        arxiv_id=arxiv_id,
        doi=doi,
    )

    if not results:
        return f"No metadata found for {cite_key}"

    best = max(results, key=lambda r: r.confidence)

    entry = BibEntry(
        entry_type="article",
        cite_key=cite_key,
        title=best.title,
        authors=best.authors,
        year=best.year,
        doi=best.doi,
        arxiv_id=best.arxiv_id,
        journal=best.journal,
        volume=best.volume,
        pages=best.pages,
    )

    return entry_to_bibtex(entry)


async def enrich_bib_file(file_path: str) -> str:
    """Enrich all entries in a BibTeX file."""
    entries = parse_bib_file(file_path)
    enriched_count = 0

    updated_entries = []
    for entry in entries:
        results = await scrape_metadata(
            title=entry.title,
            arxiv_id=entry.arxiv_id,
            doi=entry.doi,
        )

        if results:
            best = max(results, key=lambda r: r.confidence)
            updated = _merge_metadata(entry, best)
            updated_entries.append(updated)
            enriched_count += 1
        else:
            updated_entries.append(entry)

    write_bib_file(updated_entries, file_path)

    return f"Enriched {enriched_count}/{len(entries)} entries in {file_path}"


# Register MCP tools
@mcp.tool()
async def mcp_enrich_bib_entry(
    cite_key: str,
    title: str | None = None,
    arxiv_id: str | None = None,
    doi: str | None = None,
) -> str:
    """Enrich a bibliography entry by scraping metadata.

    Args:
        cite_key: The citation key for the entry
        title: Paper title to search for
        arxiv_id: arXiv ID (e.g., 2401.12345)
        doi: DOI of the paper

    Returns:
        BibTeX string with enriched metadata
    """
    return await enrich_bib_entry(cite_key, title, arxiv_id, doi)


@mcp.tool()
async def mcp_enrich_bib_file(file_path: str) -> str:
    """Enrich all entries in a BibTeX file.

    Args:
        file_path: Path to the .bib file

    Returns:
        Summary of enriched entries
    """
    return await enrich_bib_file(file_path)


def main():
    """Run the MCP server."""
    mcp.run()
