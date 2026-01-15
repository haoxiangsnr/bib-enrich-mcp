"""Tests for BibTeX parsing functionality."""

import pytest
from bib_enrich_mcp.bib_parser import (
    BibEntry,
    parse_bib_file,
    parse_bib_string,
    entry_to_bibtex,
    write_bib_file,
)


class TestBibEntry:
    """Tests for BibEntry dataclass."""

    def test_create_entry_with_required_fields(self):
        """Test creating a BibEntry with minimal required fields."""
        entry = BibEntry(
            entry_type="article",
            cite_key="smith2023",
            title="A Great Paper",
        )
        assert entry.entry_type == "article"
        assert entry.cite_key == "smith2023"
        assert entry.title == "A Great Paper"

    def test_create_entry_with_all_fields(self):
        """Test creating a BibEntry with all optional fields."""
        entry = BibEntry(
            entry_type="inproceedings",
            cite_key="doe2024neurips",
            title="Deep Learning Advances",
            authors=["John Doe", "Jane Smith"],
            year="2024",
            venue="NeurIPS",
            doi="10.1234/example.doi",
            arxiv_id="2401.12345",
            url="https://arxiv.org/abs/2401.12345",
            abstract="This paper presents...",
            booktitle="Advances in Neural Information Processing Systems",
            journal=None,
            volume="37",
            pages="1-10",
            publisher="NeurIPS Foundation",
            raw_fields={"keywords": "deep learning, neural networks"},
        )
        assert entry.authors == ["John Doe", "Jane Smith"]
        assert entry.year == "2024"
        assert entry.doi == "10.1234/example.doi"


class TestParseBibString:
    """Tests for parsing BibTeX strings."""

    def test_parse_simple_article(self):
        """Test parsing a simple article entry."""
        bib_string = """
        @article{smith2023paper,
            title = {A Simple Paper Title},
            author = {Smith, John and Doe, Jane},
            year = {2023},
            journal = {Nature},
        }
        """
        entries = parse_bib_string(bib_string)
        assert len(entries) == 1
        assert entries[0].cite_key == "smith2023paper"
        assert entries[0].title == "A Simple Paper Title"
        assert entries[0].year == "2023"

    def test_parse_inproceedings(self):
        """Test parsing an inproceedings entry (conference paper)."""
        bib_string = """
        @inproceedings{doe2024neurips,
            title = {Conference Paper Title},
            author = {Doe, Jane},
            booktitle = {NeurIPS 2024},
            year = {2024},
        }
        """
        entries = parse_bib_string(bib_string)
        assert len(entries) == 1
        assert entries[0].entry_type == "inproceedings"
        assert entries[0].booktitle == "NeurIPS 2024"

    def test_parse_entry_with_arxiv(self):
        """Test parsing entry with arXiv information."""
        bib_string = """
        @misc{arxiv2024,
            title = {ArXiv Paper},
            author = {Researcher, A.},
            eprint = {2401.12345},
            archiveprefix = {arXiv},
            primaryclass = {cs.LG},
            year = {2024},
        }
        """
        entries = parse_bib_string(bib_string)
        assert len(entries) == 1
        assert entries[0].arxiv_id == "2401.12345"

    def test_parse_multiple_entries(self):
        """Test parsing multiple entries."""
        bib_string = """
        @article{paper1,
            title = {First Paper},
            year = {2023},
        }
        @article{paper2,
            title = {Second Paper},
            year = {2024},
        }
        """
        entries = parse_bib_string(bib_string)
        assert len(entries) == 2

    def test_parse_empty_string(self):
        """Test parsing empty string returns empty list."""
        entries = parse_bib_string("")
        assert entries == []


class TestParseBibFile:
    """Tests for parsing BibTeX files."""

    def test_parse_bib_file(self, tmp_path):
        """Test parsing a .bib file from disk."""
        bib_content = """
        @article{test2023,
            title = {Test Paper},
            author = {Test Author},
            year = {2023},
        }
        """
        bib_file = tmp_path / "test.bib"
        bib_file.write_text(bib_content)

        entries = parse_bib_file(str(bib_file))
        assert len(entries) == 1
        assert entries[0].cite_key == "test2023"

    def test_parse_nonexistent_file_raises(self):
        """Test that parsing nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_bib_file("/nonexistent/path/file.bib")


class TestEntryToBibtex:
    """Tests for converting BibEntry back to BibTeX string."""

    def test_entry_to_bibtex_article(self):
        """Test converting article entry to BibTeX."""
        entry = BibEntry(
            entry_type="article",
            cite_key="smith2023",
            title="A Great Paper",
            authors=["John Smith", "Jane Doe"],
            year="2023",
            journal="Nature",
            volume="123",
            pages="1-10",
            doi="10.1234/nature.2023",
        )
        bibtex = entry_to_bibtex(entry)
        assert "@article{smith2023," in bibtex
        assert "title = {A Great Paper}" in bibtex
        assert "author = {John Smith and Jane Doe}" in bibtex
        assert "year = {2023}" in bibtex
        assert "doi = {10.1234/nature.2023}" in bibtex

    def test_entry_to_bibtex_inproceedings(self):
        """Test converting inproceedings entry to BibTeX."""
        entry = BibEntry(
            entry_type="inproceedings",
            cite_key="doe2024",
            title="Conference Paper",
            authors=["Jane Doe"],
            year="2024",
            booktitle="ICML 2024",
        )
        bibtex = entry_to_bibtex(entry)
        assert "@inproceedings{doe2024," in bibtex
        assert "booktitle = {ICML 2024}" in bibtex


class TestWriteBibFile:
    """Tests for writing BibTeX files."""

    def test_write_bib_file(self, tmp_path):
        """Test writing entries to a .bib file."""
        entries = [
            BibEntry(
                entry_type="article",
                cite_key="paper1",
                title="First Paper",
                year="2023",
            ),
            BibEntry(
                entry_type="article",
                cite_key="paper2",
                title="Second Paper",
                year="2024",
            ),
        ]
        output_file = tmp_path / "output.bib"
        write_bib_file(entries, str(output_file))

        content = output_file.read_text()
        assert "@article{paper1," in content
        assert "@article{paper2," in content
        assert "First Paper" in content
        assert "Second Paper" in content
