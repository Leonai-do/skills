# performance-fixes Specification

## Purpose
TBD - created by archiving change extend-sitemap-advanced-features. Update Purpose after archive.
## Requirements
### Requirement: Domain lock prevents SSRF attacks

The skill SHALL domain lock prevents ssrf attacks.

**Why**: Malicious sitemaps could point to internal IPs or external sites.

**Impact**: Security hardening for production use.

#### Scenario: Block external domain requests

**Given**: Processing `https://example.com/sitemap.xml`

**When**: Sitemap contains URL `https://evil.com/malware`

**Then**:

- If `--domain-lock` enabled, URL is rejected
- Only URLs from `example.com` domain are processed
- Logged as security violation

#### Scenario: Allow subdomains

**Given**: Base URL `https://example.com`

**When**: Sitemap contains `https://docs.example.com/page`

**Then**:

- Subdomain is allowed (same parent domain)
- Processing continues normally

### Requirement: Disk space guard prevents exhaustion

The skill SHALL disk space guard prevents exhaustion.

**Why**: Large crawls can fill disk, causing system failures.

**Impact**: Production stability.

#### Scenario: Abort when disk space low

**Given**: Disk has 50MB free space remaining

**When**: About to write a new file

**Then**:

- Disk usage check runs before write
- Check determines < 100MB threshold
- Write aborted with error: "Insufficient disk space"
- Crawl terminates gracefully with partial manifest

### Requirement: Max file size prevents memory exhaustion

The skill SHALL max file size prevents memory exhaustion.

**Why**: Single 500MB HTML page can crash the process.

**Impact**: Stability for large sites.

#### Scenario: Skip oversized page

**Given**: URL returns `Content-Length: 52428800` (50MB)

**When**: `--max-file-size 10` (10MB limit) is set

**Then**:

- Response rejected before download
- URL marked as skipped with reason "exceeds size limit"
- Processing continues to next URL

### Requirement: Async I/O provides 3-5× speedup with concurrency

The skill SHALL async i/o provides 3-5× speedup with concurrency.

**Why**: Sequential fetching is slow; async allows parallelism.

**Impact**: Crawl 10k pages in 30 minutes instead of 3 hours.

#### Scenario: Parallel page fetching

**Given**: 100 URLs to process, `--concurrency 5`

**When**: Using async I/O

**Then**:

- 5 requests in flight simultaneously
- Total time ~20 seconds (vs 100 seconds sequential)
- 5× speedup achieved

### Requirement: Connection pooling reuses TCP connections

The skill SHALL connection pooling reuses tcp connections.

**Why**: TCP handshake overhead adds 50-200ms per request.

**Impact**: 10-20% speed improvement.

#### Scenario: Reuse connections to same domain

**Given**: Processing 1000 URLs from `example.com`

**When**: HTTP client uses connection pool

**Then**:

- Only 1-2 TCP connections opened
- Subsequent requests reuse existing connections
- Significant latency reduction

### Requirement: Bloom filter reduces memory usage 10×

The skill SHALL filter URLs based on bloom filter reduces memory usage 10× to reduce crawl scope.

**Why**: Set of 1M URLs consumes ~500MB RAM; Bloom filter uses ~50MB.

**Impact**: Handle massive sitemaps (1M+ URLs) on low-memory systems.

#### Scenario: Process 1 million URLs

**Given**: Sitemap with 1M URLs

**When**: Using Bloom filter for duplicate detection

**Then**:

- Memory usage stays under 100MB
- Duplicate detection still works (with 0.1% false positive rate)
- Crawl completes successfully on 1GB RAM system

### Requirement: Collision resolution prevents file overwrites

The skill SHALL collision resolution prevents file overwrites.

**Why**: Current `resolve_collision` function exists but is unused.

**Impact**: Prevent data loss when URL paths collide.

#### Scenario: Handle path collision

**Given**:

- URL `https://example.com/page` saves to `page.md`
- URL `https://example.com/page/` also wants to save to `page/index.md`

**When**: Collision detected

**Then**:

- Second file renamed to `page_alt.md` or `page_<hash>.md`
- Both files saved without loss
- Collision logged for user review

---

