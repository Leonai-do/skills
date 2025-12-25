---
name: url_to_pdf
description: Downloads a URL and saves it as a PDF file using Playwright.
schema_source: url_to_pdf.py
---

# Url To Pdf

## Description

Downloads a URL and saves it as a PDF file with high fidelity using Playwright.

## Usage

### Execution (Modern `uv run`)

```bash
uv run tools/skills/url_to_pdf/url_to_pdf.py --url <TARGET_URL> [--name <OUTPUT_FILENAME>]
```

### Parameters

- `--url`: The full HTTP/HTTPS URL to capture (Required).
- `--name`: Custom filename for the output PDF, without extension (Optional).

### Examples

**Basic usage:**

```bash
uv run tools/skills/url_to_pdf/url_to_pdf.py --url https://example.com
```

**Custom filename:**

```bash
uv run tools/skills/url_to_pdf/url_to_pdf.py --url https://google.com --name search_page
```

### Outputs

Files are saved to: `tools/skills/url_to_pdf/output/{YYYY-MM-DD}/`

## Executable

Path: `tools/skills/url_to_pdf/url_to_pdf.py`
