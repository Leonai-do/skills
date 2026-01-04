# Tasks: Add Sitemap-to-Markdown Skill

## Phase 1: Skill Initialization

- [x] 1.1 Run `init_skill.py sitemap_to_markdown --path skills-repository/`
  - **Acceptance**: Directory `skills-repository/sitemap_to_markdown/` created with template SKILL.md
  - **Dependency**: None

- [x] 1.2 Create directory structure per compliance requirements
  - **Acceptance**: `tests/`, `tests/fixtures/`, `output/` directories exist
  - **Dependency**: 1.1

---

## Phase 2: SKILL.md and Documentation

- [x] 2.1 Create SKILL.md with YAML frontmatter
  - **Acceptance**: Contains `name`, `description`, `schema_source` fields
  - **Verification**: YAML frontmatter parses correctly
  - **Dependency**: 1.2

- [x] 2.2 Add Decision Logic section to SKILL.md
  - **Acceptance**: IF/THEN guardrails for sitemap discovery failure, rate limit exhaustion
  - **Dependency**: 2.1

- [x] 2.3 Create README.md for human documentation
  - **Acceptance**: Installation, usage examples, CLI reference documented
  - **Dependency**: 2.1

---

## Phase 3: Core Implementation

### 3A: Script Foundation

- [x] 3.1 Create sitemap_to_markdown.py with shebang and PEP 723 header
  - **Acceptance**: `#!/usr/bin/env python3` and `# /// script` block present
  - **Dependency**: 1.2

- [x] 3.2 Implement Pydantic InputModel and OutputModel
  - **Acceptance**: Models match spec (url, rate_limit, batch_size inputs; status, data, error outputs)
  - **Dependency**: 3.1

- [x] 3.3 Implement Typer CLI with all options
  - **Acceptance**: `--url`, `--output`, `--rate-limit`, `--batch-size`, `--schema` functional
  - **Dependency**: 3.2

- [x] 3.4 Implement schema discovery mode
  - **Acceptance**: `--schema` prints JSON schema to stdout
  - **Dependency**: 3.3

### 3B: Sitemap Discovery

- [x] 3.5 Implement sitemap discovery with priority algorithm
  - **Acceptance**: Checks direct URL, /sitemap.xml, /sitemap_index.xml, robots.txt in order
  - **Dependency**: 3.3

- [x] 3.6 Implement sitemap validation function
  - **Acceptance**: Returns True only for valid XML sitemaps; handles HTTP errors
  - **Dependency**: 3.5

### 3C: XML Parsing

- [x] 3.7 Implement streaming XML parser with iterparse
  - **Acceptance**: Uses `ET.iterparse()` with `elem.clear()` for memory efficiency
  - **Dependency**: 3.6

- [x] 3.8 Handle sitemap index files (recursive parsing)
  - **Acceptance**: Extracts child sitemap URLs, processes each sequentially
  - **Dependency**: 3.7

- [x] 3.9 Extract URL metadata (lastmod, changefreq, priority)
  - **Acceptance**: Metadata included in output when available
  - **Dependency**: 3.7

### 3D: Rate Limiting and Resilience

- [x] 3.10 Implement rate limiting with configurable delay
  - **Acceptance**: Default 1 req/sec, respects `--rate-limit` option
  - **Dependency**: 3.7

- [x] 3.11 Implement exponential backoff with jitter
  - **Acceptance**: Formula: `min(base * 2^retry, max) + random(0,1)`
  - **Dependency**: 3.10

- [x] 3.12 Handle HTTP 429 with Retry-After header
  - **Acceptance**: Respects Retry-After if present, else uses backoff
  - **Dependency**: 3.11

### 3E: Checkpointing

- [x] 3.13 Implement checkpoint save (every 100 URLs)
  - **Acceptance**: Checkpoint JSON saved to `output/<domain>/checkpoint.json`
  - **Dependency**: 3.9

- [x] 3.14 Implement checkpoint resume on restart
  - **Acceptance**: Skips already-processed URLs, continues from last position
  - **Dependency**: 3.13

### 3F: Output Generation

- [x] 3.15 Implement hierarchical URL grouping by path
  - **Acceptance**: URLs grouped under `### /path/segment` headers
  - **Dependency**: 3.9

- [x] 3.16 Generate Markdown with metadata
  - **Acceptance**: Includes `# Sitemap:`, Generated timestamp, Total URLs, URL list
  - **Dependency**: 3.15

- [x] 3.17 Implement domain-based output directory
  - **Acceptance**: Files saved to `output/<sanitized-domain>/sitemap-<timestamp>.md`
  - **Dependency**: 3.16

- [x] 3.18 Implement path traversal protection
  - **Acceptance**: Rejects paths containing `..` or outside workspace
  - **Dependency**: 3.17

### 3G: Error Handling

- [x] 3.19 Implement structured JSON error responses
  - **Acceptance**: All errors return `{"status": "error", "error": "message"}`
  - **Dependency**: 3.18

- [x] 3.20 Implement logging to stderr
  - **Acceptance**: Progress, rate limit events logged as `[LOG] message` to stderr
  - **Dependency**: 3.19

---

## Phase 4: Testing

- [x] 4.1 Create test fixtures: `sample_sitemap.xml` (10 URLs)
  - **Acceptance**: Valid XML with `<urlset>` and `<url>` elements
  - **Dependency**: 1.2

- [x] 4.2 Create test fixtures: `sample_sitemap_index.xml` (2 sitemaps)
  - **Acceptance**: Valid XML with `<sitemapindex>` and `<sitemap>` elements
  - **Dependency**: 4.1

- [x] 4.3 Write pytest tests for discovery module
  - **Acceptance**: Tests for direct URL, fallback discovery, robots.txt parsing
  - **Dependency**: 3.6, 4.1

- [x] 4.4 Write pytest tests for XML parser
  - **Acceptance**: Tests for valid XML, malformed XML, namespace handling
  - **Dependency**: 3.9, 4.1

- [x] 4.5 Write pytest tests for rate limiting
  - **Acceptance**: Tests for backoff timing, jitter presence
  - **Dependency**: 3.11

- [x] 4.6 Write pytest tests for checkpoint save/load
  - **Acceptance**: Tests for checkpoint creation, resume from checkpoint
  - **Dependency**: 3.14, 4.1

- [x] 4.7 Write pytest tests for path validation
  - **Acceptance**: Tests for rejected traversal attempts, allowed paths
  - **Dependency**: 3.18

- [x] 4.8 Run full test suite
  - **Acceptance**: All tests pass
  - **Dependency**: 4.3-4.7

---

## Phase 5: Validation

- [x] 5.1 Run `skills-ref validate`
  - **Acceptance**: No errors from skills-ref validation tool
  - **Dependency**: Phase 3 complete

- [x] 5.2 Run `package_skill.py` validation
  - **Acceptance**: Skill passes packaging validation
  - **Dependency**: 5.1

- [x] 5.3 Run schema discovery test
  - **Acceptance**: `--schema` outputs valid JSON schema
  - **Dependency**: 5.2

- [x] 5.4 Run integration test with live sitemap
  - **Acceptance**: Successfully processes `https://www.sitemaps.org/sitemap.xml`
  - **Dependency**: 5.3

- [x] 5.5 Verify output file structure
  - **Acceptance**: Markdown file created in `output/www.sitemaps.org/`
  - **Dependency**: 5.4

---

## Phase 6: Finalization

- [x] 6.1 Create output/.gitignore
  - **Acceptance**: Contains `*` and `!.gitignore`
  - **Dependency**: 5.5

- [x] 6.2 Update openspec/specs/sitemap-to-markdown/spec.md
  - **Acceptance**: Spec delta archived, capability documented
  - **Dependency**: 5.5

- [x] 6.3 Generate skill creation report
  - **Acceptance**: Report created in `docs/docs-local/<date>/`
  - **Dependency**: 6.2

- [x] 6.4 Git sync changes
  - **Acceptance**: All files committed and pushed
  - **Dependency**: 6.3

---

## Summary

| Phase             | Tasks | Dependencies |
| ----------------- | ----- | ------------ |
| 1. Initialization | 2     | None         |
| 2. Documentation  | 3     | Phase 1      |
| 3. Implementation | 20    | Phase 1-2    |
| 4. Testing        | 8     | Phase 3      |
| 5. Validation     | 5     | Phase 3-4    |
| 6. Finalization   | 4     | Phase 5      |

**Total Tasks: 42**  
**Parallelizable**: Tasks 4.1-4.2 can run parallel to Phase 3  
**Critical Path**: 1.1 → 3.1 → 3.3 → 3.7 → 3.16 → 4.8 → 5.4 → 6.4
