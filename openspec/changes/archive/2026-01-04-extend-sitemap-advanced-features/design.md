# Design: Extend Sitemap to Markdown with Advanced Features

## Architecture Overview

The enhancement organizes features into **7 independent modules** that extend the core `sitemap_to_markdown` skill without breaking existing functionality.

```
sitemap_to_markdown.py (main)
├── Core (existing)
│   ├── Sitemap discovery
│   ├── XML parsing
│   ├── Rate limiting
│   └── Checkpointing
│
├── [NEW] filters.py (Phase 1)
│   ├── regex_filter()
│   ├── path_filter()
│   ├── priority_filter()
│   └── changefreq_filter()
│
├── [NEW] extractors.py (Phase 2)
│   ├── extract_main_content()
│   ├── download_images()
│   ├── convert_pdf()
│   └── extract_with_selectors()
│
├── [NEW] network.py (Phase 3)
│   ├── AsyncHTTPClient
│   ├── ProxyManager
│   └── RobotsParser
│
├── [NEW] reporters.py (Phase 4)
│   ├── ProgressTracker
│   ├── HTMLReportGenerator
│   ├── DiffCalculator
│   └── WebhookNotifier
│
├── [NEW] storage.py (Phase 5)
│   ├── FormatConverter (JSON/HTML/Text)
│   ├── ArchiveBuilder
│   ├── SQLiteStore
│   └── S3Uploader
│
└── [NEW] ai_integrations.py (Phase 6)
    ├── Summarizer
    ├── EntityExtractor
    └── SemanticChunker
```

## Key Design Decisions

### 1. Backward Compatibility

**Decision**: All new features are **opt-in** via CLI flags.

**Rationale**: Existing users can continue using the skill without changes. Default behavior remains unchanged (process entire sitemap, output Markdown).

**Implementation**:

- Default values for all new flags = `None` or `False`
- Check `if inputs.new_feature:` before executing new logic

### 2. Modular vs Monolithic

**Decision**: Keep implementation in **single file** for Phases 1-4, **split into modules** for Phases 5-6 if needed.

**Rationale**:

- **Pro (monolithic)**: Simpler deployment, no import path issues, PEP 723 works
- **Con (monolithic)**: Large file (~2000 lines after all phases)
- **Pro (modular)**: Better code organization, easier testing
- **Con (modular)**: Harder to package as single-file skill

**Compromise**:

- Phases 1-4: Inline in main file (most common features)
- Phases 5-6: Optional modules loaded dynamically if dependencies available

### 3. Async vs Sync

**Decision**: Implement **async-optional** pattern (Phase 3).

**Rationale**:

- Some users won't have async libraries installed
- Async provides 3-5× speedup but adds complexity
- Must maintain sync fallback for compatibility

**Implementation**:

```python
try:
    import httpx
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

if inputs.concurrency > 1 and ASYNC_AVAILABLE:
    await process_async(...)
else:
    process_sync(...)
```

### 4. Filter Composition

**Decision**: Filters are **ANDed** (all must pass).

**Example**:

```bash
--include-pattern "^.*/docs/.*$" --exclude-paths "/docs/old" --priority-min 0.5
```

→ URL must match pattern AND not be in `/docs/old/` AND have priority ≥ 0.5

**Rationale**: More restrictive is safer. Users can always run multiple passes for OR logic.

### 5. Content Processing Pipeline

**Decision**: Process in **fixed order** (Phase 2):

1. Fetch HTML
2. Extract main content (if `--extract-main`)
3. Apply custom selectors (if provided)
4. Remove unwanted elements (scripts, styles)
5. Download images/assets (if enabled)
6. Convert to Markdown
7. Post-process (cleanup newlines, etc.)

**Rationale**: Order matters. For example, must extract main content BEFORE applying selectors, otherwise selectors might fail.

### 6. Storage Abstraction

**Decision**: Create **StorageBackend** interface (Phase 5):

```python
class StorageBackend:
    def save(self, url: str, content: str, metadata: dict): ...
    def exists(self, url: str) -> bool: ...
    def get(self, url: str) -> str: ...

class FileSystemBackend(StorageBackend): ...
class SQLiteBackend(StorageBackend): ...
class S3Backend(StorageBackend): ...
```

**Rationale**: Allows switching storage without changing core logic. Supports multiple simultaneous backends (save to both filesystem AND S3).

### 7. Error Handling Strategy

**Decision**: Implement **configurable error behavior** (Phase 7):

- `--on-error skip` (default): Log error, continue
- `--on-error retry`: Retry 3× with backoff, then skip
- `--on-error abort`: Stop entire crawl on first error

**Rationale**: Different use cases need different behavior:

- **skip**: CI/CD jobs (want partial success)
- **retry**: Production crawls (want reliability)
- **abort**: Testing (want to catch errors immediately)

### 8. Checkpoint Evolution

**Decision**: Upgrade checkpoint version from v2 → v3 to add new fields:

```json
{
  "version": 3,
  "started_at": "...",
  "source_url": "...",
  "processed_urls": [...],
  "failed_urls": [...],
  "skipped_urls": [...],
  "filtered_urls": [...],  // NEW
  "partial_downloads": {   // NEW (for resume)
    "example.com/page": {"bytes_downloaded": 50000}
  }
}
```

**Backward Compatibility**: Load v2 checkpoints, upgrade on save.

### 9. AI Integration Safety

**Decision**: Never auto-send content to AI APIs without explicit flag (Phase 6).

**Rationale**: Privacy/compliance. Users must explicitly opt-in with `--summarize` and provide API key.

**Implementation**:

```python
if inputs.summarize:
    if not inputs.ai_api_key:
        log("ERROR: --summarize requires --ai-api-key")
        sys.exit(1)
    # Proceed with API calls
```

### 10. Performance Optimization Priority

**Decision**: Fix bugs (Phase 7) BEFORE adding performance features (Phase 3).

**Rationale**:

1. Correctness > Speed
2. Bug fixes are smaller, lower risk
3. Users can immediately benefit from fixes without new dependencies

**Order**: Phase 7 → Phase 1 → Phase 2 → Phase 4 → Phase 3 → Phase 5 → Phase 6

## Data Flow Diagrams

### Current Flow (Before Enhancements)

```
URL Input → Discover Sitemap → Parse URLs → [For Each URL] → Fetch → Convert → Save → Manifest
```

### Enhanced Flow (After All Phases)

```
URL Input
  ↓
Discover Sitemap
  ↓
Parse URLs → [Phase 1: Filter] → Filtered Queue
  ↓
[Phase 3: Async Batch]
  ├─> [Parallel] Fetch URL 1 → [Phase 2: Process] → [Phase 5: Store]
  ├─> [Parallel] Fetch URL 2 → [Phase 2: Process] → [Phase 5: Store]
  └─> [Parallel] Fetch URL 3 → [Phase 2: Process] → [Phase 5: Store]
  ↓
[Phase 4: Generate Reports]
  ├─> HTML Report
  ├─> Progress File
  └─> Webhook Notification
  ↓
[Phase 6: AI Post-Processing] (optional)
  ├─> Summarization
  ├─> Entity Extraction
  └─> Semantic Chunking
  ↓
Final Manifest + Archive
```

## Testing Strategy Per Phase

| Phase         | Unit Tests             | Integration Tests       | Benchmark Tests     |
| ------------- | ---------------------- | ----------------------- | ------------------- |
| 1 - Filtering | Regex matching         | Real sitemap filter     | N/A                 |
| 2 - Content   | Readability extraction | PDF conversion          | N/A                 |
| 3 - Network   | Async logic            | Proxy + concurrency     | Sequential vs async |
| 4 - Reporting | HTML template render   | End-to-end report       | N/A                 |
| 5 - Storage   | Format conversion      | S3 upload               | N/A                 |
| 6 - AI        | Mock API calls         | Real API (requires key) | N/A                 |
| 7 - Perf/Bugs | Timestamp comparison   | Resume from checkpoint  | Bloom filter memory |

## Migration Path for Users

Users can adopt phases incrementally:

**Week 1**: Upgrade to Phase 7 (bug fixes only)

- No new features, just stability improvements
- **Risk**: Very low

**Week 2**: Enable Phase 1 (filtering)

- Start using `--include-pattern` to reduce crawl scope
- **Risk**: Low (just skipping URLs, not changing processing)

**Week 3**: Enable Phase 2 (content quality)

- Add `--extract-main` for cleaner output
- **Risk**: Medium (changes output format)

**Week 4**: Enable Phase 4 (monitoring)

- Add `--html-report` for visibility
- **Risk**: Low (just adds output files)

**Optional**: Phases 3, 5, 6 as needed

- Phase 3 if speed is critical
- Phase 5 if integration is needed
- Phase 6 if AI features are wanted

## Security Considerations

### 1. Path Traversal (Existing + Phase 5)

- **Risk**: Malicious sitemap could specify URLs like `../../etc/passwd`
- **Mitigation**: Already implemented `validate_output_path`, ensure applied to all storage backends

### 2. SSRF (Server-Side Request Forgery)

- **Risk**: Sitemap points to internal IPs (e.g., `http://192.168.1.1/admin`)
- **Mitigation**: Add domain lock (Phase 7): `--domain-lock` flag prevents external requests

### 3. Disk Exhaustion

- **Risk**: Crawling 1M page site fills disk
- **Mitigation**: Implement disk guard (incomplete in current code)
  - Check `shutil.disk_usage()` before every write
  - Abort if free space < 100MB

### 4. AI API Key Exposure

- **Risk**: API key in CLI history or logs
- **Mitigation**:
  - Support env var: `SITEMAP_AI_API_KEY`
  - Never log full key (log `sk-...***` instead)
  - Document in `SKILL.md`: "Use env var for production"

### 5. Dependency Supply Chain

- **Risk**: Malicious code in `pypdf`, `spacy`, etc.
- **Mitigation**:
  - Pin exact versions in PEP 723 header
  - Only install optional deps when feature is used
  - Document supply chain in README

## Open Questions

1. **Q**: Should we support custom Markdown converters (not just `html2text`)?
   - **A**: Consider in Phase 2.6 (future work). For now, `html2text` is sufficient.

2. **Q**: How to handle very large pages (50MB+ HTML)?
   - **A**: Add `--max-page-size` flag in Phase 7.8. Skip pages larger than threshold.

3. **Q**: Should AI features work offline (e.g., local models)?
   - **A**: Out of scope for Phase 6.0. Could be Phase 6.5 (future).

4. **Q**: Should we support GraphQL-based sitemaps or only XML?
   - **A**: Out of scope. Stick to XML sitemap protocol.

5. **Q**: How to handle dynamic content (JavaScript-rendered pages)?
   - **A**: Requires headless browser (Playwright). Too complex for current scope. Document as limitation.

## Success Metrics

After implementing all phases, we should see:

| Metric                                | Before | After (Target)             |
| ------------------------------------- | ------ | -------------------------- |
| Avg crawl speed (pages/sec)           | 1.0    | 3-5 (with `--concurrency`) |
| Memory usage (100k URLs)              | ~500MB | ~50MB (with Bloom filter)  |
| User adoption (GitHub stars)          | 10     | 50+ (within 3 months)      |
| Issue reports for bugs                | 5 open | 0 (after Phase 7)          |
| Feature requests addressing filtering | 3      | 0 (after Phase 1)          |
