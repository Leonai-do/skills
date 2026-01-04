# Implementation Tasks: Enhance Sitemap Content Mirroring

> **Completion Criteria**: All tasks marked `[x]`, `openspec validate enhance-sitemap-content-mirroring --strict` passes, manual verification against `docs.crewai.com` succeeds.

---

## Phase 1: Core Functionality

### 1.1 URL→Path Algorithm

- [x] 1.1.1 Create `url_to_filepath(url: str, base_dir: Path) -> Path` function
- [x] 1.1.2 Strip URL fragments (`#section`)
- [x] 1.1.3 Handle query strings: if present, append `__q_{hash8}.md`
- [x] 1.1.4 URL-decode path, sanitize to filesystem-safe characters
- [x] 1.1.5 Enforce 255-char filename limit with hash fallback
- [x] 1.1.6 Resolve `foo` vs `foo/` collision (always use `foo/index.md` pattern)
- [x] 1.1.7 **Test**: Unit tests for 10+ edge cases (colons, slashes, unicode, long paths)

### 1.2 Content Fetching & Conversion

- [x] 1.2.1 Add `beautifulsoup4>=4.12,<5.0` to script dependencies
- [x] 1.2.2 Create `fetch_and_convert(url: str, timeout: int) -> tuple[str, dict]` function
- [x] 1.2.3 Validate `Content-Type` header is `text/html*`; skip otherwise
- [x] 1.2.4 Preprocess HTML: remove `<script>`, `<style>`, `<nav>`, `<footer>` tags
- [x] 1.2.5 Absolutify relative URLs (`src="/x"` → `src="https://domain.com/x"`)
- [x] 1.2.6 Convert to Markdown via `markdownify`
- [x] 1.2.7 Add metadata frontmatter: `source_url`, `fetched_at`, `content_type`
- [x] 1.2.8 **Test**: Mock HTML with relative images → verify absolute in output

### 1.3 Rate Limiting for Content

- [x] 1.3.1 Ensure `rate_limit_sleep()` called before every `requests.get()` in content fetch
- [x] 1.3.2 Add `--content-rate-limit` CLI flag (default: same as sitemap rate)
- [x] 1.3.3 **Test**: Time 10 content fetches, verify elapsed ≥ expected delay

---

## Phase 2: Robustness & Resumability

### 2.1 Checkpoint Redesign

- [x] 2.1.1 Extend `Checkpoint` model: add `processed_urls_file: str` field
- [x] 2.1.2 On each URL processed, append to `_processed.txt` (one URL per line)
- [x] 2.1.3 On resume, load `_processed.txt` into `seen_urls: Set[str]`
- [x] 2.1.4 Skip URLs already in `seen_urls`
- [x] 2.1.5 Handle corrupt checkpoint: log warning, rename to `.corrupt`, start fresh
- [x] 2.1.6 **Test**: Start crawl, kill at 50%, resume → verify no re-processing

### 2.2 Error Isolation

- [x] 2.2.1 Add `--on-error` CLI flag with choices: `skip` (default), `retry`, `abort`
- [x] 2.2.2 Create `_failed.log` file: append `{timestamp}\t{url}\t{error}` on failure
- [x] 2.2.3 On `skip`: log to `_failed.log`, continue to next URL
- [x] 2.2.4 On `abort`: raise exception after logging
- [x] 2.2.5 Create placeholder file `_failed/{url_hash}.md` with error details
- [x] 2.2.6 **Test**: Mock 403 response → verify logged and skipped

### 2.3 Retry Queue

- [x] 2.3.1 Define transient error codes: 500, 502, 503, 504, ConnectionError, Timeout
- [x] 2.3.2 On transient error, add URL to `retry_queue: list[str]`
- [x] 2.3.3 After main crawl, process `retry_queue` with 3× attempts and 2× delay
- [x] 2.3.4 Only mark as failed after retry exhaustion
- [x] 2.3.5 **Test**: Mock 503 → 200 → verify retry succeeds

### 2.4 Duplicate Detection

- [x] 2.4.1 Maintain `seen_urls: Set[str]` during crawl
- [x] 2.4.2 On redirect, resolve to final URL before adding to set
- [x] 2.4.3 Parse `<link rel="canonical">` and use canonical URL if present
- [x] 2.4.4 Log duplicates: `[SKIP] Duplicate: {url} → {canonical}`
- [x] 2.4.5 **Test**: Sitemap with 5 duplicates → verify only 1 fetched

---

## Phase 3: Operational Safety

### 3.1 Disk Guard

- [x] 3.1.1 Add `--max-pages` CLI flag (default: 10000)
- [x] 3.1.2 Count URLs from sitemap before crawling; warn if > max
- [x] 3.1.3 Check `shutil.disk_usage()` before each write; abort if <100MB free
- [x] 3.1.4 **Test**: Set `--max-pages=5`, provide 10-URL sitemap → verify stops at 5

### 3.2 Content Validation

- [x] 3.2.1 Check `Content-Type` response header before processing
- [x] 3.2.2 If not `text/html*`, create `_skipped/{url_hash}.md` with reason
- [x] 3.2.3 Log: `[SKIP] Non-HTML: {url} (Content-Type: application/pdf)`
- [x] 3.2.4 **Test**: Mock PDF URL → verify skipped with placeholder

### 3.3 Progress Reporting

- [x] 3.3.1 Write `_progress.json` every 100 URLs: `{processed, total, elapsed_sec, eta_sec}`
- [x] 3.3.2 Print to stderr: `[{processed}/{total}] Processing: {url}`
- [x] 3.3.3 Calculate ETA based on average time per URL
- [x] 3.3.4 **Test**: Crawl 200 URLs → verify 2 progress updates

### 3.4 Manifest Generation

- [x] 3.4.1 Create `_manifest.json`: `{version, crawl_date, total, failed, skipped, pages: [{url, path, size}]}`
- [x] 3.4.2 Create `_index.md`: Table of contents grouped by path, links to local `.md` files
- [x] 3.4.3 Include failed/skipped counts in metadata
- [x] 3.4.4 **Test**: Verify manifest validates against JSON schema

---

## Phase 4: Incremental Updates

### 4.1 Update Mode

- [x] 4.1.1 Add `--update` CLI flag
- [x] 4.1.2 If output directory exists, load previous `_manifest.json`
- [x] 4.1.3 For each URL: compare sitemap `lastmod` vs local file mtime
- [x] 4.1.4 Only fetch if `lastmod > mtime` or file doesn't exist
- [x] 4.1.5 Update manifest with new/changed entries
- [x] 4.1.6 **Test**: Create file with old mtime → verify re-fetched

### 4.2 Security Hardening

- [x] 4.2.1 Use `Path.resolve(strict=True)` to resolve symlinks
- [x] 4.2.2 Verify resolved path is within allowed output directory
- [x] 4.2.3 **Test**: Create symlink escape attempt → verify rejected

---

## Phase 5: Documentation & Finalization

### 5.1 Update SKILL.md

- [x] 5.1.1 Rename skill description to reflect content mirroring
- [x] 5.1.2 Add CLI option documentation for all new flags
- [x] 5.1.3 Add example: `--update` mode for incremental crawl
- [x] 5.1.4 Add decision logic for error handling behaviors

### 5.2 Code Quality

- [x] 5.2.1 Standardize User-Agent across skills: `AgentSkills/1.0 (+https://github.com/LeonAI-DO/Agent-Skills)`
- [x] 5.2.2 Pin dependency versions in script header
- [x] 5.2.3 Add `skill_version: "2.0.0"` to manifest output
- [x] 5.2.4 Fix documentation paths in `url_to_markdown/SKILL.md`

### 5.3 Final Validation

- [x] 5.3.1 Run `openspec validate enhance-sitemap-content-mirroring --strict`
- [x] 5.3.2 Run all unit tests
- [x] 5.3.3 Execute manual verification against `docs.crewai.com`
- [x] 5.3.4 Generate walkthrough documenting test results

---

## Dependencies

```
Phase 1 ─┬─► Phase 2 ─┬─► Phase 3 ─► Phase 4 ─► Phase 5
         │            │
         │            └─► (2.1-2.4 can run concurrently after 1.2 done)
         │
         └─► (1.1-1.3 can run concurrently)
```

## Estimated Effort

| Phase     | Tasks  | Estimated Hours |
| --------- | ------ | --------------- |
| Phase 1   | 19     | 6-8             |
| Phase 2   | 21     | 6-8             |
| Phase 3   | 15     | 4-5             |
| Phase 4   | 9      | 3-4             |
| Phase 5   | 12     | 2-3             |
| **Total** | **76** | **21-28**       |
