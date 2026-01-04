# sitemap-content-mirroring Specification

## Purpose
TBD - created by archiving change enhance-sitemap-content-mirroring. Update Purpose after archive.
## Requirements
### Requirement: URL-to-Filesystem Path Mapping

The system SHALL convert URLs to local filesystem paths using a deterministic, reversible algorithm.

#### Scenario: Standard URL path mapping

- **WHEN** processing URL `https://docs.example.com/api/users/create`
- **THEN** the system creates file at `output/docs.example.com/api/users/create/index.md`

#### Scenario: Query string handling

- **WHEN** processing URL `https://example.com/search?q=test&page=2`
- **THEN** the system creates file at `output/example.com/search__q_{hash8}.md` where `{hash8}` is the first 8 characters of MD5 hash of `q=test&page=2`

#### Scenario: Fragment stripping

- **WHEN** processing URL `https://example.com/docs#installation`
- **THEN** the system strips the fragment and maps to `output/example.com/docs/index.md`

#### Scenario: Filename length enforcement

- **WHEN** processing a URL where the resulting filename exceeds 200 characters
- **THEN** the system truncates the filename and appends `_{hash8}.md` for uniqueness

---

### Requirement: HTML Content Fetching and Conversion

The system SHALL fetch HTML content from URLs and convert it to Markdown format.

#### Scenario: Successful HTML conversion

- **WHEN** fetching a URL that returns `Content-Type: text/html`
- **THEN** the system converts the HTML to Markdown using ATX-style headings and saves to the mapped filepath

#### Scenario: Non-HTML content handling

- **WHEN** fetching a URL that returns `Content-Type: application/pdf`
- **THEN** the system creates a placeholder file in `_skipped/` directory with the URL and content type information

#### Scenario: Relative URL absolutification

- **WHEN** HTML contains `<img src="/images/logo.png">`
- **THEN** the system converts it to `![](/images/logo.png)` → `![](https://example.com/images/logo.png)` in the Markdown output

#### Scenario: Script and style removal

- **WHEN** HTML contains `<script>` or `<style>` tags
- **THEN** the system removes these tags before Markdown conversion to prevent content pollution

---

### Requirement: Rate Limiting for Content Fetches

The system SHALL enforce rate limiting on all HTTP requests to prevent server overload.

#### Scenario: Default rate limiting

- **WHEN** crawling with default settings
- **THEN** the system waits at least 1 second between each content fetch request

#### Scenario: Custom rate limit

- **WHEN** user specifies `--content-rate-limit 0.5`
- **THEN** the system waits at least 2 seconds between each content fetch request

#### Scenario: 429 response handling

- **WHEN** server returns HTTP 429 (Too Many Requests)
- **THEN** the system applies exponential backoff with jitter, respecting `Retry-After` header if present

---

### Requirement: Resumable Checkpoint System

The system SHALL support interruption and resume of long-running crawls.

#### Scenario: Checkpoint creation

- **WHEN** processing URLs during a crawl
- **THEN** the system appends each processed URL to `_processed.txt` immediately after successful save

#### Scenario: Resume from checkpoint

- **WHEN** starting a crawl and `_processed.txt` exists in the output directory
- **THEN** the system loads the file into a set and skips any URLs already present

#### Scenario: Corrupt checkpoint recovery

- **WHEN** checkpoint file contains invalid JSON or is corrupted
- **THEN** the system logs a warning, renames the file to `.corrupt`, and starts fresh

---

### Requirement: Error Isolation Strategy

The system SHALL handle individual page failures without aborting the entire crawl.

#### Scenario: Skip mode (default)

- **WHEN** a page fetch fails and `--on-error=skip` is set
- **THEN** the system logs the failure to `_failed.log`, creates a placeholder in `_failed/`, and continues

#### Scenario: Abort mode

- **WHEN** a page fetch fails and `--on-error=abort` is set
- **THEN** the system saves the checkpoint and exits with a non-zero status code

#### Scenario: Transient error retry

- **WHEN** a page returns HTTP 503 and `--on-error=retry` is set
- **THEN** the system adds the URL to a retry queue, processes it after the main crawl with 3 attempts

---

### Requirement: Disk Space Guard

The system SHALL prevent disk exhaustion during large crawls.

#### Scenario: Max pages limit

- **WHEN** user specifies `--max-pages 1000`
- **THEN** the system stops crawling after processing 1000 pages successfully

#### Scenario: Disk space check

- **WHEN** available disk space falls below 100MB during crawl
- **THEN** the system saves checkpoint and aborts gracefully with a clear error message

---

### Requirement: Duplicate URL Detection

The system SHALL avoid processing the same content multiple times.

#### Scenario: Explicit duplicate

- **WHEN** sitemap contains the same URL twice
- **THEN** the system processes it only once

#### Scenario: Redirect deduplication

- **WHEN** URL A redirects to URL B, and both are in sitemap
- **THEN** the system uses the final URL (B) for deduplication

#### Scenario: Canonical URL detection

- **WHEN** page contains `<link rel="canonical" href="https://example.com/canonical">`
- **THEN** the system uses the canonical URL for deduplication when available

---

### Requirement: Progress Reporting

The system SHALL provide visibility into crawl progress for long-running operations.

#### Scenario: Stderr progress output

- **WHEN** processing URLs
- **THEN** the system prints `[{processed}/{total}] Processing: {url}` to stderr

#### Scenario: Progress file updates

- **WHEN** every 100 URLs are processed
- **THEN** the system writes `_progress.json` with `processed`, `total`, `elapsed_sec`, and `eta_sec`

---

### Requirement: Manifest and Index Generation

The system SHALL generate navigable outputs for the crawled content.

#### Scenario: Manifest creation

- **WHEN** crawl completes successfully
- **THEN** the system creates `_manifest.json` containing version, crawl metadata, and list of all pages with paths and sizes

#### Scenario: Index creation

- **WHEN** crawl completes successfully
- **THEN** the system creates `_index.md` with a table of contents grouped by path hierarchy with links to local `.md` files

---

### Requirement: Incremental Update Mode

The system SHALL support updating existing mirrors without re-downloading unchanged content.

#### Scenario: Update mode activation

- **WHEN** user specifies `--update` and output directory exists
- **THEN** the system loads previous `_manifest.json` and compares sitemap `lastmod` against local file mtime

#### Scenario: Selective re-fetching

- **WHEN** sitemap entry has `lastmod` newer than local file mtime
- **THEN** the system re-fetches and overwrites only that page

#### Scenario: New page detection

- **WHEN** sitemap contains a URL not present in previous manifest
- **THEN** the system fetches and saves the new page

---

### Requirement: Security Path Validation

The system SHALL prevent path traversal attacks in output file generation.

#### Scenario: Symlink escape prevention

- **WHEN** resolving output filepath
- **THEN** the system uses `Path.resolve(strict=True)` and verifies the resolved path is within the allowed output directory

#### Scenario: Parent directory traversal

- **WHEN** URL path contains `../` sequences
- **THEN** the system normalizes the path and rejects any result outside the output directory

