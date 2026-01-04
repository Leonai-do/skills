# Spec: Performance Improvements & Bug Fixes

## ADDED Requirements

### Requirement: Update mode correctly compares timestamps

The skill MUST compare sitemap lastmod timestamps against file modification times to determine if re-fetch is needed.

**Previous**: Update mode existed but didn't properly compare sitemap `lastmod` vs file modification time

**Now**: Update mode parses timestamps and skips only if local file is newer

**Why**: Current implementation just checks file existence, not freshness.

#### Scenario: Re-fetch outdated local copy

**Given**:

- Local file `docs/page.md` exists with mtime `2025-01-01 10:00:00`
- Sitemap shows `<lastmod>2026-01-02</lastmod>` for that URL

**When**: User runs with `--update`

**Then**:

- Timestamp comparison occurs
- File is determined to be stale
- Page is re-downloaded
- File mtime updated to current time

#### Scenario: Skip up-to-date local copy

**Given**:

- Local file exists with mtime `2026-01-03 10:00:00`
- Sitemap shows `<lastmod>2026-01-02</lastmod>`

**When**: User runs with `--update`

**Then**:

- File is newer than sitemap's lastmod
- Download is skipped
- Processing continues to next URL

### Requirement: Rate limiting applies only once per request

The skill SHALL enforce rate limiting in exactly one location to avoid double-delay penalties.

**Previous**: Rate limit sleep called in both main loop AND `fetch_with_retry`

**Now**: Rate limit sleep only in main loop before calling `process_url`

**Why**: Double sleeping causes 2× slower crawls than necessary.

#### Scenario: Sequential request timing

**Given**: Rate limit set to 1.0 req/sec

**When**: Processing 10 URLs sequentially

**Then**:

- Total time is ~10 seconds (1 sec per URL)
- NOT ~20 seconds (double rate limiting)
- One sleep per URL, not two

### Requirement: Checkpoint saves on keyboard interrupt

The skill MUST save checkpoint state before exiting when interrupted by user.

**Previous**: Ctrl+C just logged and exited without saving state

**Now**: Checkpoint saved before exit

**Why**: Losing progress on accidental Ctrl+C is frustrating.

#### Scenario: User interrupts long crawl

**Given**: Crawl in progress, 500 URLs processed

**When**: User presses Ctrl+C

**Then**:

- Checkpoint written with 500 processed URLs
- Exit code 130 (standard for SIGINT)
- On restart, crawl resumes from URL 501

---

## ADDED Requirements

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

## REMOVED Requirements

None. All changes are additive or corrections.

---

## Technical Specifications

### Timestamp Comparison

```python
from dateutil import parser
from datetime import datetime
from pathlib import Path

def should_update_file(url: str, meta: dict, local_path: Path) -> bool:
    if not local_path.exists():
        return True  # File doesn't exist, must fetch

    lastmod = meta.get('lastmod')
    if not lastmod:
        return False  # No timestamp in sitemap, assume current file is fine

    try:
        lastmod_dt = parser.parse(lastmod)
        file_mtime_dt = datetime.fromtimestamp(local_path.stat().st_mtime)

        # Re-fetch if sitemap is newer
        return lastmod_dt > file_mtime_dt
    except Exception as e:
        log(f"Timestamp parse error: {e}, defaulting to update")
        return True  # On error, err on side of updating
```

### Domain Lock

```python
def check_domain_lock(url: str, base_domain: str, enable_lock: bool) -> bool:
    if not enable_lock:
        return True  # Lock disabled, allow all

    url_domain = urlparse(url).netloc

    # Extract TLD+1 (e.g., "example.com" from "docs.example.com")
    # Simple implementation: check if ends with base domain
    if url_domain == base_domain or url_domain.endswith(f".{base_domain}"):
        return True

    log(f"Domain lock violation: {url} not in {base_domain}")
    return False
```

### Disk Space Check

```python
import shutil

def check_disk_space(path: Path, required_mb: int = 100) -> bool:
    usage = shutil.disk_usage(path)
    free_mb = usage.free / (1024 * 1024)

    if free_mb < required_mb:
        log(f"Insufficient disk space: {free_mb:.1f}MB free, need {required_mb}MB")
        return False

    return True
```

### Async Refactor

```python
import httpx
import asyncio

async def process_url_async(url: str, output_dir: Path, semaphore: asyncio.Semaphore):
    async with semaphore:  # Limit concurrency
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            # ... rest of processing
            return "success"

async def main_async(urls: List[str], concurrency: int):
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [process_url_async(url, output_dir, semaphore) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### Bloom Filter

```python
from pybloom_live import BloomFilter

# Instead of:
processed_set = set()

# Use:
processed_bloom = BloomFilter(capacity=1000000, error_rate=0.001)

# Usage:
if url in processed_bloom:
    continue  # Already processed (or false positive <0.1%)
processed_bloom.add(url)
```

## Acceptance Criteria

- [ ] `--update` mode timestamp comparison tested with mock files
- [ ] Double rate-limiting confirmed fixed (benchmark shows 2× speedup)
- [ ] Ctrl+C saves checkpoint (manual test)
- [ ] `--domain-lock` prevents external URLs (security test)
- [ ] Disk space check prevents writes when <100MB free
- [ ] `--max-file-size` rejects oversized responses
- [ ] `--concurrency 5` achieves 3-5× speedup (benchmark)
- [ ] Connection pooling reduces latency by 10-20% (benchmark)
- [ ] Bloom filter handles 1M URLs in <100MB RAM (memory profiling)
- [ ] Collision resolution test with conflicting paths

## Cross-References

- **Fixes**: Issues in `sitemap-content-mirroring` spec
- **Enables**: `network-crawling` spec (async/concurrency)
- **Required by**: All other phases (stability foundation)
