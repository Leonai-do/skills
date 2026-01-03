# Sitemap to Markdown

Convert XML sitemaps to structured Markdown documentation with support for large-scale processing, rate limiting, and automatic discovery.

## Installation

This skill has no additional dependencies beyond the Python standard library and common packages already used in the Agent Skills project:

```bash
# Dependencies (via PEP 723 header)
- Python 3.11+
- typer
- pydantic
- requests
```

## Quick Start

### Automatic Discovery

```bash
python sitemap_to_markdown.py --url "https://example.com"
```

The skill will automatically search for sitemaps at:

1. Direct URL (if it ends with `.xml`)
2. `/sitemap.xml`
3. `/sitemap_index.xml`
4. `robots.txt` Sitemap directive

### Direct Sitemap URL

```bash
python sitemap_to_markdown.py --url "https://example.com/sitemap.xml"
```

### Custom Rate Limiting

```bash
python sitemap_to_markdown.py --url "https://example.com" --rate-limit 2
```

Sets the rate to 2 requests per second (default is 1).

### Large Sites

```bash
python sitemap_to_markdown.py --url "https://large-site.com" --batch-size 500
```

Processes URLs in batches of 500 (default is 1000).

## CLI Reference

| Option         | Type   | Default  | Description                           |
| -------------- | ------ | -------- | ------------------------------------- |
| `--url`        | string | required | Base URL or direct sitemap URL        |
| `--output`     | path   | auto     | Custom output file path               |
| `--rate-limit` | float  | 1.0      | Requests per second                   |
| `--batch-size` | int    | 1000     | URLs processed per batch              |
| `--schema`     | flag   | -        | Print InputModel JSON schema and exit |

## Output

### Markdown File

Saved to `output/<domain>/sitemap-<timestamp>.md`:

```markdown
# Sitemap: example.com

**Generated**: 2026-01-03 16:20:00 UTC
**Total URLs**: 1,523
**Source**: https://example.com/sitemap.xml

## URLs by Section

### /products

- [Product A](https://example.com/products/a) - _lastmod: 2026-01-01_
- [Product B](https://example.com/products/b) - _lastmod: 2026-01-02_

### /blog

- [Post 1](https://example.com/blog/post-1) - _lastmod: 2025-12-15_
```

### JSON Response

```json
{
  "status": "success",
  "data": {
    "url": "https://example.com",
    "sitemap_url": "https://example.com/sitemap.xml",
    "total_urls": 1523,
    "saved_to": "/path/to/output/example.com/sitemap-20260103-162000.md",
    "markdown_preview": "# Sitemap: example.com\n\n**Generated**: 2026-01-03..."
  }
}
```

## Features

### Memory Efficient

Uses streaming XML parser (`iterparse`) with element clearing - processes 50K+ URL sitemaps with constant memory usage.

### Resumable

Saves checkpoint every 100 URLs. If interrupted (Ctrl+C), resume from last position on restart.

### Respectful Crawling

- Default 1 request/second rate limiting
- Exponential backoff for HTTP 429 responses
- Respects `Retry-After` headers
- Jitter to avoid thundering herd

### Security

- Path traversal protection
- Validates all output paths
- Rejects paths containing `..` or outside workspace

## Troubleshooting

### "No sitemap found"

Ensure the site has a sitemap at one of the standard locations or explicitly provide the sitemap URL.

### "Rate limit exceeded"

Decrease `--rate-limit` value or wait before retrying.

### Incomplete processing

Check for checkpoint file in `output/<domain>/checkpoint.json`. The skill will resume automatically on restart.

## Testing

Run the test suite:

```bash
pytest tests/
```

## License

Part of the LeonAI_DO Agent Skills project.
