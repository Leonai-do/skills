# Change: Enhance Sitemap to Full Site Content Mirroring

## Why

The current `sitemap_to_markdown` skill only **lists** URLs from a sitemap. Users need it to **download and convert** the actual page content to Markdown, creating a local mirror of the site's documentation. A comprehensive [critique analysis](file:///home/leonai-do/.gemini/antigravity/brain/e76e1f82-3d23-4d97-a329-20dcf3fd552a/critique_report.md) identified **8 critical, 11 major, and 6 minor issues** that must be addressed for production-scale crawling (50k+ pages, 14+ hour runs).

## What Changes

### Phase 1: Core Functionality

- **URL→Path Algorithm** — Define complete mapping: strip fragments, hash query strings, enforce 255-char limit, resolve `foo` vs `foo/` collisions
- **Content Fetching** — Integrate `url_to_markdown` logic: fetch HTML, validate Content-Type, preprocess (strip scripts/styles), convert to Markdown
- **Rate Limiting** — Ensure rate limiting applies to content fetches (not just sitemap fetches)
- **HTML Preprocessing** — Absolutify relative URLs (`src="/logo.png"` → full URL), strip non-content tags

### Phase 2: Robustness & Resumability

- **Checkpoint Redesign** — Track `processed_urls: Set[str]` instead of just count; enable true resume
- **Error Isolation** — Add `--on-error=skip|retry|abort` flag, log failures to `_failed.log`
- **Retry Queue** — Collect transient failures (5xx, timeout), retry 3× after main crawl
- **Duplicate Detection** — Deduplicate by final URL after redirects; consider canonical tag parsing

### Phase 3: Operational Safety

- **Disk Guard** — Add `--max-pages` limit (default: 10,000), check <100MB free before writes
- **Content Validation** — Skip non-HTML (PDF, images) with placeholder in `_skipped/`
- **Progress Reporting** — Write `_progress.json`, print `[1234/50000] Processing: ...` to stderr
- **Manifest Generation** — Create `_index.md` (human) and `_manifest.json` (machine)

### Phase 4: Incremental Updates

- **Update Mode** — Add `--update` flag: compare `lastmod` vs local mtime, overwrite only changed pages
- **Symlink Security** — Resolve symlinks with `resolve(strict=True)` to prevent path traversal

### Phase 5 (Optional): Advanced Features

- `--respect-robots` flag for ethical crawling
- `--timeout` configuration
- `--max-depth` option
- `--concurrency` for parallel crawl (future)

## Test Strategy

### Automated Tests

1. **URL→Path mapping** — Unit tests for query strings, fragments, collisions, encoding
2. **Checkpoint serialization** — Test save/load with 10k URLs, verify resume skips processed
3. **Content-Type validation** — Mock server returning PDF/JSON, verify graceful skip
4. **HTML preprocessing** — Verify script/style removal, relative URL absolutification
5. **Rate limiting** — Time 10 requests, verify ≥9 seconds elapsed

### Integration Tests

1. Mock sitemap with 100 URLs → verify 100 `.md` files in correct directory structure
2. Simulate transient failure → verify retry queue processes
3. Corrupt checkpoint → verify graceful recovery (log + reset)

### Manual Verification

- Target: `https://docs.crewai.com/sitemap.xml` (small, stable)
- Criteria:
  - ≥90% pages converted
  - 0 uncaught exceptions
  - Directory structure mirrors URL paths
  - Images render as remote URLs in markdown
  - `_manifest.json` and `_index.md` generated

## Impact

- **Affected specs**: `sitemap-content-mirroring` (new capability)
- **Affected code**:
  - `skills-repository/sitemap_to_markdown/sitemap_to_markdown.py`
  - `skills-repository/sitemap_to_markdown/SKILL.md`
  - `skills-repository/url_to_markdown/url_to_markdown.py` (minor fixes)
- **Breaking changes**: None (new mode, existing behavior preserved via flags)
