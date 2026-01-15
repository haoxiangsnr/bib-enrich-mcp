"""BibTeX parsing and writing functionality."""

from dataclasses import dataclass, field
from pathlib import Path

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase


@dataclass
class BibEntry:
    """Represents a bibliography entry."""

    entry_type: str
    cite_key: str
    title: str
    authors: list[str] | None = None
    year: str | None = None
    venue: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    url: str | None = None
    abstract: str | None = None
    booktitle: str | None = None
    journal: str | None = None
    volume: str | None = None
    pages: str | None = None
    publisher: str | None = None
    raw_fields: dict[str, str] = field(default_factory=dict)


def _parse_authors(author_string: str | None) -> list[str] | None:
    """Parse author string into list of author names."""
    if not author_string:
        return None
    authors = [a.strip() for a in author_string.split(" and ")]
    return authors if authors else None


def _extract_arxiv_id(entry: dict) -> str | None:
    """Extract arXiv ID from entry fields."""
    if "eprint" in entry:
        return entry["eprint"]
    if "arxiv" in entry:
        return entry["arxiv"]
    return None


def _dict_to_bib_entry(entry: dict) -> BibEntry:
    """Convert bibtexparser dict entry to BibEntry."""
    raw_fields = {
        k: v
        for k, v in entry.items()
        if k
        not in (
            "ENTRYTYPE",
            "ID",
            "title",
            "author",
            "year",
            "doi",
            "url",
            "abstract",
            "booktitle",
            "journal",
            "volume",
            "pages",
            "publisher",
            "eprint",
            "arxiv",
        )
    }

    return BibEntry(
        entry_type=entry.get("ENTRYTYPE", "misc"),
        cite_key=entry.get("ID", ""),
        title=entry.get("title", ""),
        authors=_parse_authors(entry.get("author")),
        year=entry.get("year"),
        doi=entry.get("doi"),
        arxiv_id=_extract_arxiv_id(entry),
        url=entry.get("url"),
        abstract=entry.get("abstract"),
        booktitle=entry.get("booktitle"),
        journal=entry.get("journal"),
        volume=entry.get("volume"),
        pages=entry.get("pages"),
        publisher=entry.get("publisher"),
        raw_fields=raw_fields,
    )


def parse_bib_string(bib_string: str) -> list[BibEntry]:
    """Parse a BibTeX string and return list of BibEntry objects."""
    if not bib_string.strip():
        return []

    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    bib_db = bibtexparser.loads(bib_string, parser=parser)

    return [_dict_to_bib_entry(entry) for entry in bib_db.entries]


def parse_bib_file(file_path: str) -> list[BibEntry]:
    """Parse a BibTeX file and return list of BibEntry objects."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"BibTeX file not found: {file_path}")

    with open(path, encoding="utf-8") as f:
        return parse_bib_string(f.read())


def _bib_entry_to_dict(entry: BibEntry) -> dict:
    """Convert BibEntry to bibtexparser dict format."""
    result = {
        "ENTRYTYPE": entry.entry_type,
        "ID": entry.cite_key,
        "title": entry.title,
    }

    if entry.authors:
        result["author"] = " and ".join(entry.authors)
    if entry.year:
        result["year"] = entry.year
    if entry.doi:
        result["doi"] = entry.doi
    if entry.arxiv_id:
        result["eprint"] = entry.arxiv_id
    if entry.url:
        result["url"] = entry.url
    if entry.abstract:
        result["abstract"] = entry.abstract
    if entry.booktitle:
        result["booktitle"] = entry.booktitle
    if entry.journal:
        result["journal"] = entry.journal
    if entry.volume:
        result["volume"] = entry.volume
    if entry.pages:
        result["pages"] = entry.pages
    if entry.publisher:
        result["publisher"] = entry.publisher

    result.update(entry.raw_fields)
    return result


def entry_to_bibtex(entry: BibEntry) -> str:
    """Convert a BibEntry to BibTeX string format."""
    db = BibDatabase()
    db.entries = [_bib_entry_to_dict(entry)]

    writer = BibTexWriter()
    writer.indent = "  "
    return writer.write(db).strip()


def write_bib_file(entries: list[BibEntry], file_path: str) -> None:
    """Write list of BibEntry objects to a BibTeX file."""
    db = BibDatabase()
    db.entries = [_bib_entry_to_dict(e) for e in entries]

    writer = BibTexWriter()
    writer.indent = "  "

    path = Path(file_path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(writer.write(db))
