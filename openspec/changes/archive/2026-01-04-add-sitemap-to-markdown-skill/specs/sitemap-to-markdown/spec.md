## ADDED Requirements

### Requirement: Sitemap Discovery

The skill SHALL automatically discover sitemap URLs using a priority-based algorithm.

The discovery priority order SHALL be:

1. If input URL ends with `.xml`, use it directly
2. Try `<base_url>/sitemap.xml`
3. Try `<base_url>/sitemap_index.xml`
4. Parse `<base_url>/robots.txt` for `Sitemap:` directives

The skill SHALL return an error if no valid sitemap is found.

#### Scenario: Direct XML URL provided

- **WHEN** user provides `--url "https://example.com/sitemap.xml"`
- **THEN** the skill validates and uses that URL directly

#### Scenario: Base URL with existing sitemap

- **WHEN** user provides `--url "https://example.com"` and `/sitemap.xml` exists
- **THEN** the skill discovers and uses `https://example.com/sitemap.xml`

#### Scenario: Sitemap in robots.txt

- **WHEN** user provides `--url "https://example.com"` and sitemap is only in robots.txt
- **THEN** the skill extracts sitemap URL from `Sitemap:` directive

#### Scenario: No sitemap found

- **WHEN** no valid sitemap exists at any location
- **THEN** the skill returns `{"status": "error", "error": "No sitemap found at any location"}`

---

### Requirement: Streaming XML Parser

The skill SHALL parse XML sitemaps using a streaming approach for memory efficiency.

The parser SHALL use `xml.etree.ElementTree.iterparse()` with element clearing.

The skill SHALL support both single sitemaps (`<urlset>`) and sitemap indexes (`<sitemapindex>`).

#### Scenario: Large sitemap parsing

- **WHEN** parsing a sitemap with 50,000+ URLs
- **THEN** memory usage remains constant (no full DOM load)

#### Scenario: Sitemap index processing

- **WHEN** parsing a `<sitemapindex>` file
- **THEN** the skill extracts child sitemap URLs and processes each sequentially

#### Scenario: Malformed XML handling

- **WHEN** encountering malformed XML entries
- **THEN** the skill logs the error to stderr and continues processing valid entries

---

### Requirement: Rate Limiting

The skill SHALL implement rate limiting to respect server resources.

The default rate limit SHALL be 1 request per second.

The skill SHALL support configurable rate limits via `--rate-limit` option.

The skill SHALL implement exponential backoff with jitter for HTTP 429 responses.

#### Scenario: Default rate limiting

- **WHEN** processing multiple sitemap requests
- **THEN** requests are spaced at minimum 1 second apart

#### Scenario: Custom rate limit

- **WHEN** user specifies `--rate-limit 2`
- **THEN** requests are spaced at minimum 0.5 seconds apart

#### Scenario: HTTP 429 response

- **WHEN** server returns HTTP 429 (Too Many Requests)
- **THEN** the skill applies exponential backoff with formula: `min(base * 2^retry, 60) + random(0,1)`

---

### Requirement: Checkpointing

The skill SHALL save progress checkpoints to support resumable processing.

Checkpoints SHALL be saved every 100 URLs processed.

Checkpoint files SHALL be stored in the output directory as `checkpoint.json`.

On restart, the skill SHALL detect and resume from existing checkpoints.

#### Scenario: Checkpoint creation

- **WHEN** 100 URLs have been processed
- **THEN** a checkpoint file is saved with current progress

#### Scenario: Resume from checkpoint

- **WHEN** skill is restarted with existing checkpoint
- **THEN** processing resumes from last saved position

#### Scenario: Checkpoint cleanup

- **WHEN** processing completes successfully
- **THEN** the checkpoint file is removed

---

### Requirement: Structured Output

The skill SHALL generate structured output in both Markdown and JSON formats.

The Markdown output SHALL group URLs hierarchically by path segments.

The JSON output SHALL follow the standard Agent Skills response format.

The JSON response SHALL NOT include full markdown content for large sitemaps.

#### Scenario: Markdown file structure

- **WHEN** processing is complete
- **THEN** markdown file contains: title, metadata (generated date, total URLs, source), and grouped URL lists

#### Scenario: JSON response format

- **WHEN** processing succeeds
- **THEN** response is `{"status": "success", "data": {"url": "...", "sitemap_url": "...", "total_urls": N, "saved_to": "...", "markdown_preview": "..."}}`

#### Scenario: JSON error format

- **WHEN** processing fails
- **THEN** response is `{"status": "error", "error": "message"}`

---

### Requirement: Security Validation

The skill SHALL validate all file paths to prevent directory traversal attacks.

Output paths containing `..` SHALL be rejected.

Output paths SHALL be constrained to the designated output directory.

#### Scenario: Path traversal attempt

- **WHEN** output path contains `..`
- **THEN** the skill returns an error and does not write to that path

#### Scenario: Valid output path

- **WHEN** output path is within `output/<domain>/`
- **THEN** the skill writes the file successfully

---

### Requirement: CLI Interface

The skill SHALL provide a Typer-based CLI with self-documenting schema discovery.

Required options: `--url` (required), `--output`, `--rate-limit`, `--batch-size`, `--schema`

The `--schema` flag SHALL print the JSON schema and exit.

#### Scenario: Schema discovery

- **WHEN** user runs with `--schema`
- **THEN** skill prints InputModel JSON schema to stdout and exits

#### Scenario: Required URL option

- **WHEN** user runs without `--url`
- **THEN** skill displays usage error

#### Scenario: Custom output path

- **WHEN** user specifies `--output /path/to/file.md`
- **THEN** skill saves markdown to specified path (after validation)

---

### Requirement: Testing Infrastructure

The skill SHALL include pytest unit tests and test fixtures.

Tests SHALL cover: discovery, parsing, rate limiting, checkpointing, path validation.

Test fixtures SHALL include sample sitemap XML files.

#### Scenario: Test suite execution

- **WHEN** running `pytest tests/`
- **THEN** all tests pass

#### Scenario: Fixture availability

- **WHEN** tests require sitemap data
- **THEN** tests use fixtures in `tests/fixtures/` instead of live URLs
