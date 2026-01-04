# Change: Extend Sitemap to Markdown with Advanced Features

## Why

The current `sitemap_to_markdown` skill provides basic content mirroring but lacks critical features for production use:

1. **No Filtering**: Users must process entire sitemaps, wasting bandwidth and time on unwanted sections
2. **Limited Content Processing**: Can't extract main content only, preserve specific elements, or handle non-HTML formats
3. **Basic Monitoring**: No progress tracking, reporting, or metrics for long-running crawls
4. **Rigid Output**: Only supports Markdown files; no JSON, HTML, or database storage
5. **Missing Safety**: No disk space checks, domain validation, or file size limits
6. **Integration Gaps**: Can't be automated in cron jobs, CI/CD pipelines, or triggered by webhooks
7. **Performance Bottlenecks**: Sequential processing, no connection pooling, inefficient duplicate detection
8. **Incomplete Features**: `--update` mode doesn't properly compare timestamps, `--batch-size` is unused

These limitations prevent the skill from being used for:

- **Documentation sites** (need to filter `/docs/*` only)
- **SEO audits** (need metrics, change detection, reporting)
- **Knowledge bases** (need RAG-ready chunking, embeddings)
- **Archival** (need complete asset downloading, offline viewing)
- **CI/CD** (need automation, error handling, notifications)

## What Changes

We organize enhancements into **7 phased capabilities**, each independently valuable:

### Phase 1: Filtering & Selection

- URL pattern matching (regex include/exclude)
- Path prefix filtering (simpler than regex)
- Priority-based filtering (sitemap priority thresholds)
- Change frequency filtering

### Phase 2: Enhanced Content Processing

- Main content extraction (readability algorithm)
- Image downloading and local rewrites
- PDF/document conversion
- Custom CSS selector-based extraction
- Asset downloading for offline viewing

### Phase 3: Advanced Crawling & Network

- Concurrent request processing (async I/O)
- Proxy support
- Custom headers/authentication
- robots.txt respect
- Configurable timeouts

### Phase 4: Reporting & Monitoring

- Real-time progress files
- HTML/JSON/CSV report generation
- Diff reports (compare crawls)
- Webhook notifications (Slack, Discord)
- Prometheus metrics export

### Phase 5: Storage & Integration

- Multiple output formats (Markdown, JSON, HTML, text)
- Archive generation (tar.gz, zip)
- SQLite storage for querying
- S3/GCS upload
- Single-file mode

### Phase 6: AI/LLM Integration

- Page summarization (via API)
- Named entity extraction
- Semantic chunking for RAG
- Auto-generated TOC
- Content translation

### Phase 7: Performance & Bug Fixes

- Fix incomplete `--update` mode logic
- Fix double rate-limiting issue
- Implement unused `resolve_collision` function
- Proper Ctrl+C checkpoint saving
- Async I/O with `httpx` or `aiohttp`
- Connection pooling
- Bloom filter for memory-efficient duplicate detection

## Test Strategy

### Automated Tests (Required for Each Phase)

**Phase 1 - Filtering**:

- Unit: Test regex matching against 100 URLs (50 should match, 50 filtered)
- Integration: Crawl test sitemap with `--include-pattern "^.*/docs/.*$"`, verify only `/docs/*` saved

**Phase 2 - Content Processing**:

- Unit: Test readability extraction on sample HTML with ads/nav
- Integration: Test PDF conversion on sample PDF file
- Integration: Test image download and local path rewrite

**Phase 3 - Network**:

- Unit: Mock concurrent requests, verify parallelism
- Integration: Test with `--concurrency 3`, verify 3× speed improvement
- Integration: Test proxy with mocked proxy server

**Phase 4 - Reporting**:

- Unit: Verify `_progress.json` schema
- Integration: Run crawl, verify HTML report generated with correct stats
- Integration: Test webhook with mock HTTP server

**Phase 5 - Storage**:

- Unit: Test JSON output format serialization
- Integration: Generate SQLite DB, query for specific URL
- Integration: Create tar.gz, extract and verify contents

**Phase 6 - AI**:

- Unit: Mock API calls, verify request format
- Integration: Test summarization with real API (requires key)
- Unit: Test semantic chunking algorithm

**Phase 7 - Performance**:

- Unit: Test `--update` timestamp comparison logic
- Benchmark: Measure async vs sync performance (expect 3× improvement)
- Integration: Test Ctrl+C, verify checkpoint saved

### Manual Verification (Supplemental)

- **Target**: `https://docs.crewai.com/sitemap.xml` (small, stable)
- **Criteria per phase**:
  - Phase 1: Apply `--include-pattern`, verify filtered output
  - Phase 2: Verify main content extracted, images downloaded
  - Phase 4: Verify HTML report opens and renders correctly
  - Phase 5: Verify tar.gz contains all files

## Impact

- **Affected specs**: `sitemap-content-mirroring` (modified), 7 new phase specs
- **Affected code**:
  - `skills-repository/sitemap_to_markdown/sitemap_to_markdown.py` (all phases)
  - `skills-repository/sitemap_to_markdown/SKILL.md` (documentation update)
  - New modules: `extractors.py`, `reporters.py`, `storage.py`, `ai_integrations.py` (optional refactor)
- **Breaking changes**: None (all features opt-in via flags)
- **Dependencies added**:
  - Phase 2: `readability-lxml`, `pypdf`
  - Phase 3: `httpx` or `aiohttp`, `aiofiles`
  - Phase 4: `jinja2` (for HTML templates)
  - Phase 5: `boto3` (optional, for S3)
  - Phase 6: `openai` or `anthropic` (optional, for AI features)
  - Phase 7: `pybloom-live` (for Bloom filter)

## Phasing Strategy

Each phase is **independently deployable and valuable**:

```
Phase 1 (Filtering) ─┐
                     ├─► Can merge to main after completion
Phase 2 (Content)   ─┤
                     ├─► No dependencies between phases
Phase 3 (Network)   ─┤
                     ├─► User chooses which to implement
Phase 4 (Reporting) ─┤
                     │
Phase 5 (Storage)   ─┘
Phase 6 (AI) ────────► Optional (requires API keys)
Phase 7 (Perf/Bugs)─► Highest priority (fixes issues)
```

**Recommended order**: 7 → 1 → 2 → 4 → 3 → 5 → 6

- Start with bug fixes (Phase 7) for stability
- Add filtering (Phase 1) for immediate user value
- Add content features (Phase 2) for quality
- Add reporting (Phase 4) for visibility
- Add network features (Phase 3) for speed
- Add storage (Phase 5) for flexibility
- Add AI (Phase 6) last (requires external dependencies)
