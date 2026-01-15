# bib-enrich-mcp

[![PyPI version](https://badge.fury.io/py/bib-enrich-mcp.svg)](https://badge.fury.io/py/bib-enrich-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An MCP (Model Context Protocol) server that fixes and enriches BibTeX bibliography files with metadata from academic sources like arXiv, DBLP, and CrossRef.

## Features

- **Automatic metadata scraping** from multiple sources:
  - arXiv API
  - DBLP API
  - CrossRef API
- **BibTeX parsing and writing** with full field support
- **Batch processing** of entire .bib files
- **MCP integration** for use with AI assistants

## Installation

```bash
# Or install with uv (Recommended)
uv tool install bib-enrich-mcp

# Install from PyPI
pip install bib-enrich-mcp

# Or clone and install locally
git clone https://github.com/haoxiangsnr/bib-enrich-mcp.git
cd bib-enrich-mcp
uv sync
```

## Usage

### As an MCP Server

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "bib-enrich": {
      "command": "bib-enrich-mcp"
    }
  }
}
```

### Running the Server

```bash
bib-enrich-mcp
```

## API Documentation

### MCP Tools

#### `mcp_enrich_bib_entry`

Enrich a single bibliography entry by scraping metadata from academic sources.

**Parameters:**
- `cite_key` (required): The citation key for the entry
- `title` (optional): Paper title to search for
- `arxiv_id` (optional): arXiv ID (e.g., "2401.12345")
- `doi` (optional): DOI of the paper

**Returns:** BibTeX string with enriched metadata

**Example:**
```python
result = await mcp_enrich_bib_entry(
    cite_key="vaswani2017attention",
    title="Attention Is All You Need"
)
```

#### `mcp_enrich_bib_file`

Enrich all entries in a BibTeX file.

**Parameters:**
- `file_path` (required): Path to the .bib file

**Returns:** Summary of enriched entries

**Example:**
```python
result = await mcp_enrich_bib_file("/path/to/references.bib")
# Returns: "Enriched 5/10 entries in /path/to/references.bib"
```

### Python API

You can also use the library directly in Python:

```python
from bib_enrich_mcp.bib_parser import parse_bib_file, write_bib_file
from bib_enrich_mcp.scrapers import scrape_metadata

# Parse a bib file
entries = parse_bib_file("references.bib")

# Scrape metadata for a paper
results = await scrape_metadata(
    title="Attention Is All You Need",
    arxiv_id="1706.03762"
)
```

## Supported Metadata Sources

| Source   | Search by Title | Search by ID | Notes                   |
| -------- | --------------- | ------------ | ----------------------- |
| arXiv    | ✅               | ✅ (arXiv ID) | Best for preprints      |
| DBLP     | ✅               | ❌            | Best for CS conferences |
| CrossRef | ✅               | ✅ (DOI)      | Best for journals       |

## Development

### Running Tests

```bash
uv run pytest tests/ -v
```

### Project Structure

```
bib-enrich-mcp/
├── src/bib_enrich_mcp/
│   ├── __init__.py
│   ├── bib_parser.py    # BibTeX parsing/writing
│   ├── scrapers.py      # Metadata scrapers
│   └── server.py        # MCP server
├── tests/
│   ├── test_bib_parser.py
│   ├── test_scrapers.py
│   └── test_server.py
├── pyproject.toml
└── README.md
```

## License

MIT
