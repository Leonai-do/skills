---
name: sitemap_to_markdown
description: Converts website XML sitemaps to structured Markdown documentation with rate limiting and large file support. Use when you need to: audit website structures for SEO, generate site architecture documentation, or create markdown inventories from XML sitemaps.
schema_source: sitemap_to_markdown.py
---

# Sitemap To Markdown

## Overview

Converts XML sitemaps (single sitemaps and sitemap indexes) to structured Markdown documentation. Handles large-scale sitemaps (50K+ URLs) with memory-efficient streaming, automatic discovery, rate limiting, and resumable checkpointing.

## Core Capabilities

### 1. Automatic Sitemap Discovery

The skill autonomously locates sitemaps using a priority-based algorithm:

1. **Direct XML URL**: If `--url` ends with `.xml`, validates and uses it
2. **Common locations**: Tries `/sitemap.xml`, `/sitemap_index.xml`
3. **robots.txt parsing**: Extracts `Sitemap:` directives

**When to use**: Provide a base URL (e.g., `https://example.com`) and let the skill discover the sitemap automatically.

### 2. Large-Scale Processing

- **Streaming parser**: Uses `xml.etree.ElementTree.iterparse()` to process sitemaps without loading full DOM
- **Memory efficient**: Handles 50,000+ URLs with constant memory usage
- **Batch processing**: Configurable batch size (default: 1000 URLs)
- **Checkpoint/resume**: Saves progress every 100 URLs, resumes from interruptions

### 3. Respectful Crawling

- **Rate limiting**: Default 1 request/second, configurable via `--rate-limit`
- **Exponential backoff**: Handles HTTP 429 responses with jitter
- **Retry-After support**: Respects server-specified retry delays

### 4. Structured Output

- **Markdown**: Hierarchical URL grouping by path segments
- **JSON response**: Agent-compatible output with preview (no full markdown for large sitemaps)
- **Metadata extraction**: Includes `lastmod`, `changefreq`, `priority` when available

## Usage

This skill is a self-documenting CLI tool. Output files are saved to `output/<domain>/`.

### Discovery

Get the JSON schema for inputs:

```bash
python skills-repository/sitemap_to_markdown/sitemap_to_markdown.py --schema
```

### Execution

```bash
# Basic usage (auto-discovers sitemap)
python skills-repository/sitemap_to_markdown/sitemap_to_markdown.py --url "https://example.com"

# Direct sitemap URL
python skills-repository/sitemap_to_markdown/sitemap_to_markdown.py --url "https://example.com/sitemap.xml"

# Custom rate limit (2 requests/second)
python skills-repository/sitemap_to_markdown/sitemap_to_markdown.py --url "https://example.com" --rate-limit 2

# Large sitemap with smaller batches
python skills-repository/sitemap_to_markdown/sitemap_to_markdown.py --url "https://large-site.com" --batch-size 500
```

## CLI Options

| Option               | Type   | Default  | Description                         |
| -------------------- | ------ | -------- | ----------------------------------- |
| `--url`              | string | required | Base URL or direct sitemap URL      |
| `--output`           | path   | auto     | Custom output file path             |
| `--rate-limit`       | float  | 1.0      | Requests per second                 |
| `--batch-size`       | int    | 1000     | URLs processed per batch            |
| `--concurrency`      | int    | 5        | Max concurrent requests (async)     |
| `--update`           | flag   | -        | Only fetch new/changed pages        |
| `--max-pages`        | int    | 10000    | Max pages to process                |
| **Filtering**        |        |          |                                     |
| `--include-pattern`  | regex  | -        | Process only URLs matching regex    |
| `--exclude-pattern`  | regex  | -        | Skip URLs matching regex            |
| `--include-paths`    | string | -        | Comma-separated path prefixes       |
| `--exclude-paths`    | string | -        | Comma-separated path prefixes       |
| `--priority-min`     | float  | -        | Min sitemap priority to process     |
| `--changefreq`       | string | -        | Specific changefreq to process      |
| **Content**          |        |          |                                     |
| `--extract-main`     | flag   | -        | Use Readability for main content    |
| `--download-images`  | flag   | -        | Download images to `_assets/images` |
| `--download-assets`  | flag   | -        | Download CSS/JS to `_assets`        |
| `--pdf-support`      | flag   | -        | Convert PDF files to Text/MD        |
| `--content-selector` | css    | -        | Extract content matching CSS        |
| `--strip-selector`   | css    | -        | Remove elements matching CSS        |
| `--schema`           | flag   | -        | Print JSON schema and exit          |

## Decision Logic

The skill follows strict guardrails to ensure reliability:

### IF sitemap is not found at any location:

- **STOP**: Return error with attempted locations
- **Output**: `{"status": "error", "error": "No sitemap found at ..."}`

### IF HTTP 429 (rate limited) after max retries:

- **STOP**: Return error indicating rate limit exhaustion
- **Output**: `{"status": "error", "error": "Rate limit exceeded after 3 retries"}`

### IF malformed XML encountered:

- **CONTINUE**: Log error to stderr, skip invalid entries
- **Behavior**: Process valid URLs, report malformed entries count

### IF interrupted (Ctrl+C):

- **SAVE**: Create checkpoint file in output directory
- **Resume**: On restart, detect checkpoint and continue from last position

## Example Workflow

**Agent Request**: "I need to audit the site structure of example.com"

**Agent Action**:

1. Calls skill with `--url "https://example.com"`
2. Skill discovers sitemap at `/sitemap.xml`
3. Streams parse 5,000 URLs with rate limiting
4. Generates hierarchical markdown saved to `output/example.com/sitemap-20260103-162000.md`
5. Returns JSON with `saved_to` path and `markdown_preview`

**Agent Response**: "I've audited example.com's site structure. Found 5,000 pages organized into 12 main sections. The complete documentation is saved at [path]."

## Executable

Path: `skills-repository/sitemap_to_markdown/sitemap_to_markdown.py`
