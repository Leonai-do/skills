## Context

The `sitemap_to_markdown` skill bridges website XML sitemaps and structured Markdown documentation. This design addresses the technical challenges of:

1. **Large-scale processing**: Sitemaps can contain 50,000+ URLs
2. **Respectful crawling**: Rate limiting to avoid server overload
3. **Resilience**: Recovery from network failures and interruptions
4. **Agent integration**: Structured output for programmatic consumption

### Stakeholders

- **Agent Users**: Need automated sitemap documentation
- **Website Owners**: Their servers must not be overwhelmed
- **Skill Maintainers**: Need testable, maintainable code

### Constraints

- Must follow agentskills.io specification (PDF Section 5)
- Must use existing dependency patterns (`typer`, `pydantic`, `requests`)
- Must pass `package_skill.py` and `skills-ref validate`
- Python 3.11+ required

---

## Goals / Non-Goals

### Goals

1. Parse single sitemaps and sitemap indexes
2. Handle 50K+ URLs without memory exhaustion
3. Implement configurable rate limiting (1 req/sec default)
4. Checkpoint progress for resume on interruption
5. Generate hierarchical Markdown grouped by URL path
6. Provide structured JSON output for agents
7. Include comprehensive test suite

### Non-Goals

- Crawling actual page content (use `url_to_markdown` for that)
- Supporting compressed sitemaps (`.gz` format) — future enhancement
- Concurrent/parallel requests — complexity not justified yet
- GUI or web interface

---

## Decisions

### D1: Streaming XML Parser

**Decision**: Use `xml.etree.ElementTree.iterparse()` with element clearing

**Rationale**:

- Standard library, no additional dependencies
- Event-driven parsing prevents full DOM load
- `elem.clear()` releases memory after processing

**Alternatives Considered**:

- `lxml.etree`: Faster but adds C dependency
- `defusedxml`: Security focus overkill for trusted XML
- Full DOM parsing: Memory-prohibitive for large sitemaps

### D2: Rate Limiting Strategy

**Decision**: Token bucket with exponential backoff + jitter

**Implementation**:

```python
delay = min(base_delay * (2 ** retry_count), max_delay) + random.uniform(0, 1)
```

**Rationale**:

- Exponential backoff handles 429 (Too Many Requests) responses
- Jitter prevents thundering herd on resume
- Configurable via `--rate-limit` CLI option

**Alternatives Considered**:

- Fixed delay: Too rigid, ignores server feedback
- Leaky bucket: More complex, overkill for sequential requests

### D3: Checkpoint Format

**Decision**: JSON checkpoint file in output directory

**Format**:

```json
{
  "version": 1,
  "started_at": "ISO8601",
  "source_url": "...",
  "sitemap_type": "single|index",
  "sitemaps": [{"url": "...", "status": "completed|in_progress", "urls_processed": N}],
  "total_processed": N
}
```

**Rationale**:

- JSON is human-readable for debugging
- Version field enables format evolution
- Per-sitemap tracking handles sitemap indexes

### D4: Output Structure

**Decision**: Domain-based directories, timestamp-based filenames

**Pattern**: `output/<domain>/sitemap-<YYYYMMDD-HHMMSS>.md`

**Rationale**:

- Matches existing `url_to_markdown` pattern
- Prevents filename collisions
- Enables historical comparison

### D5: Security Model

**Decision**: Path traversal protection on output paths

**Implementation**:

```python
if ".." in path or not path.startswith(allowed_base):
    return error("Access denied: Path outside workspace")
```

**Rationale**:

- Complies with PDF Section 4.3 sandbox imperative
- Prevents skill from writing outside designated directory

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    sitemap_to_markdown.py                    │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   CLI Layer  │  Discovery   │   Parser     │   Generator    │
│   (Typer)    │   Module     │   Module     │   Module       │
├──────────────┴──────────────┴──────────────┴────────────────┤
│                    Pydantic Models                           │
│              (InputModel, OutputModel, Checkpoint)           │
├─────────────────────────────────────────────────────────────┤
│                    Core Utilities                            │
│    (rate_limit, exponential_backoff, validate_path)          │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. CLI receives --url
       │
       ▼
2. Discover sitemap (try /sitemap.xml, /sitemap_index.xml, robots.txt)
       │
       ▼
3. Parse XML (stream with iterparse)
       │  ├── If sitemap index: recurse into child sitemaps
       │  └── Checkpoint every N URLs
       ▼
4. Generate Markdown (group by path, add metadata)
       │
       ▼
5. Save to output/<domain>/sitemap-<timestamp>.md
       │
       ▼
6. Return JSON to stdout
```

---

## Risks / Trade-offs

| Risk                              | Impact                 | Mitigation                      |
| --------------------------------- | ---------------------- | ------------------------------- |
| Very large sitemaps (>100K URLs)  | Memory spike           | Streaming parser + batch writes |
| Server throttling (429 responses) | Incomplete extraction  | Exponential backoff with jitter |
| Malformed XML from third parties  | Parser crash           | try/except with graceful skip   |
| Network interruptions             | Lost progress          | Checkpoint file every 100 URLs  |
| Path traversal attacks            | File system compromise | Validate all output paths       |

---

## Open Questions

1. **Compressed sitemap support**: Should `.gz` sitemaps be handled in v1?
   - _Recommendation_: Defer to v2; prioritize core functionality
2. **Concurrent requests**: Would async requests improve performance?
   - _Recommendation_: Defer; single-threaded is simpler and respects rate limits

3. **Retry limit**: Should retries be configurable?
   - _Recommendation_: Default 3, add `--max-retries` if needed later
