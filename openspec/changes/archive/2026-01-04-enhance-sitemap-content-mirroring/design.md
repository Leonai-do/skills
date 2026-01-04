# Design: Sitemap Content Mirroring Architecture

## Context

The `sitemap_to_markdown` skill currently lists URLs from XML sitemaps. This enhancement transforms it into a full **site content mirroring** system that:

1. Discovers sitemaps (existing functionality)
2. Fetches and converts each page to Markdown (new)
3. Mirrors the site's directory structure locally (new)
4. Supports resumable, incremental crawls of 50k+ pages (new)

### Constraints

- Must handle sites with 50,000+ URLs
- Must run for 14+ hours with graceful interruption/resume
- Must not exhaust disk space or inodes
- Must respect rate limits to avoid server lockouts
- External assets (images, scripts) remain as remote URLs

### Stakeholders

- **Agent users**: Need reliable documentation mirroring for RAG/knowledge bases
- **Site operators**: Need respectful crawling (rate limits, robots.txt)

---

## Goals / Non-Goals

### Goals

- Mirror website content to local Markdown with directory structure matching URL paths
- Enable resumable crawls (checkpoint/restore)
- Provide configurable error handling and rate limiting
- Generate navigable index and machine-readable manifest

### Non-Goals

- Rewriting internal links to point to local `.md` files (complex graph problem, deferred)
- Downloading binary assets (images, PDFs) locally
- JavaScript rendering (SPAs not supported)
- Full `robots.txt` crawler compliance (optional flag only)

---

## Key Decisions

### D1: URL→Filepath Mapping Algorithm

**Decision**: Use deterministic, reversible mapping with collision prevention.

```
https://sub.domain.com/docs/api/users?page=2#section
                    ↓
output/
└── sub.domain.com/
    └── docs/
        └── api/
            └── users__q_a1b2c3d4.md   # hash of query string
```

**Rules:**

1. Strip fragments (`#section`) — they're same-page anchors
2. Subdomains → top-level directories
3. Path segments → nested directories
4. Query strings → `__q_{md5[:8]}.md` suffix
5. Trailing slash or no extension → `index.md` inside directory
6. URL-decode then sanitize (`%20` → `_`, invalid chars → `_`)
7. Max filename: 200 chars (leave room for hash suffix)

**Collision Resolution:**

- If `foo.md` exists and `foo/` needed: rename to `foo__page.md`, create `foo/index.md`
- OR: Always use `foo/index.md` pattern (every page in own directory) — **preferred for simplicity**

**Alternatives Considered:**

- Base64 encoding entire URL → unreadable, long filenames
- Flat directory with hashes → loses hierarchy, hard to navigate

### D2: Checkpoint Strategy

**Decision**: File-based checkpoint with URL set on disk.

```
output/domain.com/
├── _checkpoint.json      # Metadata: started_at, total_expected
├── _processed.txt        # One URL per line (append-only)
├── _failed.log           # Tab-separated: timestamp, url, error
└── docs/...              # Actual content
```

**Rationale:**

- `_processed.txt` is append-only → no corruption risk from crashes
- Loading 50k URLs into Set is ~5MB memory → acceptable
- Easy to inspect/debug manually

**Resume Logic:**

```python
if Path("_processed.txt").exists():
    seen = set(Path("_processed.txt").read_text().splitlines())
    for url in sitemap_urls:
        if url not in seen:
            process(url)
```

### D3: Error Handling Strategy

**Decision**: Configurable policy with three modes.

| Mode             | Behavior                                                      |
| ---------------- | ------------------------------------------------------------- |
| `skip` (default) | Log to `_failed.log`, create placeholder, continue            |
| `retry`          | Add transient errors to retry queue, process after main crawl |
| `abort`          | Log error, save checkpoint, exit immediately                  |

**Transient errors** (eligible for retry): 500, 502, 503, 504, ConnectionError, Timeout
**Permanent errors** (skip immediately): 401, 403, 404, invalid Content-Type

### D4: Rate Limiting Architecture

**Decision**: Single rate limiter for all HTTP requests, configurable separately for sitemap vs content.

```python
class RateLimiter:
    def __init__(self, requests_per_second: float):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0.0

    def wait(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()

# Usage
sitemap_limiter = RateLimiter(args.rate_limit)
content_limiter = RateLimiter(args.content_rate_limit or args.rate_limit)
```

### D5: HTML Preprocessing Pipeline

**Decision**: BeautifulSoup preprocessing before markdownify.

```python
def preprocess_html(html: str, base_url: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')

    # 1. Remove non-content elements
    for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'aside']):
        tag.decompose()

    # 2. Absolutify URLs
    for tag in soup.find_all(['a', 'img', 'link', 'script']):
        for attr in ['href', 'src']:
            if tag.has_attr(attr) and not tag[attr].startswith(('http', 'data:', '#')):
                tag[attr] = urljoin(base_url, tag[attr])

    return str(soup)
```

### D6: Output Structure

**Decision**: Generate both human-readable and machine-readable outputs.

```
output/domain.com/
├── _manifest.json        # Machine-readable: all files, metadata
├── _index.md             # Human-readable: table of contents
├── _progress.json        # Live crawl status
├── _failed.log           # Error log
├── _skipped/             # Non-HTML placeholders
│   └── {hash}.md
├── _failed/              # Error placeholders
│   └── {hash}.md
└── docs/                 # Actual content mirroring site structure
    └── api/
        └── users/
            └── index.md
```

**Manifest Schema:**

```json
{
  "version": "2.0.0",
  "source_url": "https://domain.com",
  "sitemap_url": "https://domain.com/sitemap.xml",
  "crawl_started": "2026-01-03T20:00:00Z",
  "crawl_completed": "2026-01-04T10:00:00Z",
  "total_pages": 5000,
  "successful": 4950,
  "failed": 30,
  "skipped": 20,
  "pages": [
    {
      "url": "https://...",
      "path": "docs/api/index.md",
      "size_bytes": 1234,
      "fetched_at": "..."
    }
  ]
}
```

---

## Risks / Trade-offs

| Risk                                    | Mitigation                                               |
| --------------------------------------- | -------------------------------------------------------- |
| Disk exhaustion on large sites          | `--max-pages` limit (default 10k), pre-flight disk check |
| Server lockout from aggressive crawling | Mandatory rate limiting, exponential backoff on 429      |
| Memory exhaustion loading 50k URLs      | Stream processing, append-only checkpoint file           |
| Corrupt output from crash               | Atomic writes (write to `.tmp`, rename on success)       |
| Symlink escape attack                   | `Path.resolve(strict=True)` + containment check          |

---

## Migration Plan

1. **Backward compatibility**: Existing `--url` behavior (list-only) preserved if no content flags used
2. **New default**: Add `--mirror` flag to enable content downloading
3. **Deprecation path**: In v3.0, `--mirror` becomes default, `--list-only` for old behavior

---

## Open Questions

1. **Should `--respect-robots` be opt-in or opt-out?**
   - Recommendation: Opt-in for now (default False), revisit after user feedback
2. **Concurrency level for parallel crawl?**
   - Recommendation: Defer to Phase 5; sequential is safer and simpler for MVP
3. **Should we support sitemap filtering (e.g., `--include-path=/docs/*`)?**
   - Recommendation: Add in future version if requested
