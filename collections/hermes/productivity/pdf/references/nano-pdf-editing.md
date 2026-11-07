# Natural-language PDF text editing with nano-pdf (merged from the nano-pdf skill)

Edit PDFs with natural-language instructions. Point nano-pdf at a page, describe what to change. For structural PDF work (merge, split, forms, watermarks, creation), see `pdf` skill. For text extraction from scans, see `ocr-and-documents`.

## Prerequisites

```bash
# Install with uv (recommended — already available in Hermes)
uv pip install nano-pdf

# Or with pip
pip install nano-pdf
```

## Usage

```bash
nano-pdf edit <file.pdf> <page_number> "<instruction>"
```

## Examples

```bash
# Change a title on page 1
nano-pdf edit deck.pdf 1 "Change the title to 'Q3 Results' and fix the typo in the subtitle"

# Update a date on a specific page
nano-pdf edit report.pdf 3 "Update the date from January to February 2026"

# Fix content
nano-pdf edit contract.pdf 2 "Change the client name from 'Acme Corp' to 'Acme Industries'"
```

## Notes

- Page numbers may be 0-based or 1-based depending on version. If edit hits wrong page, retry with ±1
- Always verify output PDF after editing (use `read_file` to check file size, or open it)
- Tool uses LLM under the hood: page content goes to third-party LLM API. Confirm with user before sending confidential docs; work on a copy. API key via env/config (check `nano-pdf --help`), never pasted in chat
- Works well for text changes. Complex layout modifications may need different approach
