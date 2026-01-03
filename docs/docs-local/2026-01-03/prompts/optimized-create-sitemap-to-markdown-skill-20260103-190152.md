# RAPO Optimization Report

## Metadata

- **Date**: 2026-01-03
- **Time**: 19:01:52 UTC
- **Project**: /home/leonai-do/Host-D-Drive/LeonAI_DO/dev/Agent-Skills
- **Branch**: main
- **Base Prompt**: Let's create a skill to conver any sitemap to markdown with ratelimits constraints already...

---

## Analysis Summary

### Extracted Constraints

**Security & Privacy:**

- No explicit security patterns found in existing skills beyond standard HTTP headers
- User-Agent headers used in [`url_to_markdown.py:80-82`](skills-repository/url_to_markdown/url_to_markdown.py:80-82) to avoid blocking
- No PII handling requirements detected in existing skills
- No authentication/authorization patterns found in current codebase

**Performance Requirements:**

- Timeout patterns: 30-second timeout standard in [`url_to_markdown.py:83`](skills-repository/url_to_markdown/url_to_markdown.py:83)
- Rate limiting: Not explicitly implemented in existing skills, but required for sitemap crawling
- Large file handling: No existing patterns for streaming/chunking large responses
- Memory considerations: No explicit memory management patterns found

**Architectural Patterns:**

- Self-documenting CLI tools with `--schema` flag ([`url_to_markdown.py:62-64`](skills-repository/url_to_markdown/url_to_markdown.py:62-64))
- Pydantic models for input/output validation ([`url_to_markdown.py:23-30`](skills-repository/url_to_markdown/url_to_markdown.py:23-30))
- Domain-based output directories ([`url_to_markdown.py:93-100`](skills-repository/url_to_markdown/url_to_markdown.py:93-100))
- Automatic file saving with sanitized filenames ([`url_to_markdown.py:34-49`](skills-repository/url_to_markdown/url_to_markdown.py:34-49))
- JSON output format for structured responses ([`url_to_markdown.py:125`](skills-repository/url_to_markdown/url_to_markdown.py:125))

**Coding Conventions:**

- Python 3.11+ requirement ([`url_to_markdown.py:2`](skills-repository/url_to_markdown/url_to_markdown.py:2))
- Typer for CLI argument parsing ([`url_to_markdown.py:17`](skills-repository/url_to_markdown/url_to_markdown.py:17))
- UTF-8 encoding for all file operations ([`url_to_markdown.py:107`](skills-repository/url_to_markdown/url_to_markdown.py:107))
- Error handling with structured JSON responses ([`url_to_markdown.py:72-73`](skills-repository/url_to_markdown/url_to_markdown.py:72-73))
- Logging to stderr ([`url_to_markdown.py:77`](skills-repository/url_to_markdown/url_to_markdown.py:77))

**Dependencies:**

- `typer` - CLI framework
- `pydantic` - Data validation
- `requests` - HTTP client
- `markdownify` - HTML to markdown conversion (baseline skill)
- XML parsing libraries: `xml.etree.ElementTree` (standard), `lxml` (in validation scripts)

### Architectural Patterns

**Skill Structure:**

1. **Frontmatter YAML** with `name`, `description`, optional `schema_source`
2. **SKILL.md** documentation with usage instructions
3. **Executable Python script** with:
   - Input/Output Pydantic models
   - Typer CLI interface
   - Schema discovery mode
   - Business logic with error handling
   - Automatic output directory creation

**Output Organization:**

- Domain-based subdirectories in `output/` folder
- Sanitized filenames from URLs
- Automatic directory creation with `os.makedirs(exist_ok=True)`

### Coding Conventions

**Style:**

- Type hints using `typing.Optional`
- Field descriptions in Pydantic models
- Clear docstrings for functions
- Error messages to stderr, JSON output to stdout

**Naming:**

- Kebab-case for skill names (e.g., `url_to_markdown`)
- Descriptive function names
- Clear variable names

**File Structure:**

```
skill-name/
├── SKILL.md
├── output/           # Auto-generated
│   └── domain/      # Domain-based subdirectories
└── skill_name.py     # Executable script
```

### Known Pain Points

**From Existing Skills:**

- No rate limiting implementation in current codebase
- No streaming/chunking for large files
- No retry logic for failed requests
- No progress reporting for long-running operations
- No sitemap-specific XML parsing patterns found

**Potential Issues:**

- Large sitemaps (50K+ URLs) could cause memory issues
- No handling of sitemap index files (sitemapindex)
- No support for compressed sitemaps (.gz)
- No concurrent request handling
- No resume capability for interrupted operations

### Security & Privacy

**Current Patterns:**

- User-Agent spoofing to avoid blocking ([`url_to_markdown.py:80-82`](skills-repository/url_to_markdown/url_to_markdown.py:80-82))
- No credential handling in existing skills
- No PII data processing

**Recommendations for New Skill:**

- Respect robots.txt if accessible
- Implement configurable rate limits (default: 1 request/second)
- Add timeout configuration (default: 30 seconds)
- Handle HTTP 429 (Too Many Requests) responses
- No storage of sensitive data
- Sanitize URLs before processing

### Performance Requirements

**Existing Patterns:**

- 30-second timeout standard ([`url_to_markdown.py:83`](skills-repository/url_to_markdown/url_to_markdown.py:83))
- No streaming/chunking for large responses
- No concurrent processing

**New Requirements:**

- **Rate Limiting**: Implement exponential backoff, configurable delay between requests
- **Large File Handling**: Stream sitemap parsing, process URLs in batches
- **Memory Management**: Use generators/iterators for large URL lists
- **Progress Reporting**: Log progress at intervals (every 100 URLs, etc.)
- **Resume Capability**: Save checkpoint files for interrupted operations

---

## Optimized Prompt

### Character:

You are a Python software engineer specializing in web scraping, XML parsing, and CLI tool development. You have expertise in:

- Sitemap protocol (XML sitemaps and sitemap indexes)
- Rate limiting and respectful crawling practices
- HTTP client optimization with retry logic
- Large-scale data processing with memory efficiency
- CLI tool development with Typer and Pydantic
- Agent Skills specification compliance

You prioritize:

- **Respectful crawling**: Never overwhelm servers, implement rate limits
- **Robustness**: Handle network errors, timeouts, and malformed XML gracefully
- **Scalability**: Process sitemaps with 100K+ URLs efficiently
- **User experience**: Provide clear progress feedback and error messages
- **Code quality**: Follow existing project conventions and patterns

### Request:

Create a new Agent Skill called `sitemap_to_markdown` that converts website sitemaps to structured Markdown documentation. The skill must:

**Core Functionality:**

1. Accept a URL (homepage or direct sitemap URL) as input
2. Automatically discover the sitemap (check common locations: `/sitemap.xml`, `/sitemap_index.xml`, robots.txt)
3. Parse XML sitemaps (both single sitemaps and sitemap indexes)
4. Extract all URLs with metadata (lastmod, changefreq, priority if available)
5. Export URLs to Markdown with hierarchical organization
6. Handle large sitemaps efficiently (50K+ URLs)

**Rate Limiting & Respectful Crawling:**

- Implement configurable rate limiting (default: 1 request/second)
- Add exponential backoff for HTTP 429 responses
- Respect Retry-After headers when present
- Include configurable delay between batched URL processing
- Log rate limit events to stderr
- Default User-Agent: `Mozilla/5.0 (compatible; SitemapBot/1.0; +http://example.com)`

**Large File Handling:**

- Stream XML parsing using `xml.etree.ElementTree.iterparse()` to avoid loading entire document into memory
- Process URLs in batches (configurable batch size: 1000 URLs)
- Write markdown incrementally to avoid memory buildup
- Implement checkpointing: save progress every N URLs to resume on interruption
- Use generators/iterators instead of lists where possible

**Output Format:**

- Create domain-based output directory: `output/<domain>/`
- Generate filename: `sitemap-<timestamp>.md`
- Markdown structure:

  ```markdown
  # Sitemap: <domain>

  **Generated**: YYYY-MM-DD HH:MM:SS UTC
  **Total URLs**: <count>
  **Source**: <sitemap_url>

  ## URLs by Section

  ### <path_segment>

  - [URL Title](url) - _lastmod: YYYY-MM-DD_
  ```

- Group URLs by path segments for better organization
- Include metadata when available (lastmod, changefreq, priority)

**Error Handling:**

- Network errors: Retry with exponential backoff (max 3 retries)
- Timeout errors: Log and continue with next URL
- Malformed XML: Skip invalid entries, log to stderr
- HTTP 404: Try alternative sitemap locations
- HTTP 429: Implement backoff and retry
- All errors: Return structured JSON error response

**CLI Interface:**

- `--url`: Required, the base URL or sitemap URL
- `--output`: Optional, custom output path
- `--rate-limit`: Optional, requests per second (default: 1)
- `--batch-size`: Optional, URLs per batch (default: 1000)
- `--schema`: Print JSON schema and exit
- Follow existing Typer patterns from [`url_to_markdown.py`](skills-repository/url_to_markdown/url_to_markdown.py)

**Schema Discovery:**

- Input model: Pydantic BaseModel with `url`, optional `rate_limit`, optional `batch_size`
- Output model: Pydantic BaseModel with `status`, `data` (on success), `error` (on failure)
- Schema accessible via `--schema` flag

**Dependencies:**

- `typer` - CLI framework
- `pydantic` - Data validation
- `requests` - HTTP client
- Python 3.11+ (follow [`url_to_markdown.py:2`](skills-repository/url_to_markdown/url_to_markdown.py:2))

### Examples:

**Example 1: Basic Usage**

```bash
python skills/sitemap_to_markdown/sitemap_to_markdown.py \
  --url "https://example.com"
```

**Expected Output:**

```json
{
  "status": "success",
  "data": {
    "markdown": "# Sitemap: example.com\n...",
    "url": "https://example.com",
    "sitemap_url": "https://example.com/sitemap.xml",
    "total_urls": 1523,
    "saved_to": "skills/sitemap_to_markdown/output/example.com/sitemap-20260103-190152.md"
  }
}
```

**Example 2: Custom Rate Limit**

```bash
python skills/sitemap_to_markdown/sitemap_to_markdown.py \
  --url "https://example.com" \
  --rate-limit 2
```

**Example 3: Direct Sitemap URL**

```bash
python skills/sitemap_to_markdown/sitemap_to_markdown.py \
  --url "https://example.com/sitemap.xml"
```

**Example 4: Large Sitemap (50K+ URLs)**

```bash
python skills/sitemap_to_markdown/sitemap_to_markdown.py \
  --url "https://large-site.com" \
  --batch-size 500
```

**Expected Behavior:**

- Streams XML parsing, processes in 500-URL batches
- Writes markdown incrementally
- Logs progress: `[LOG] Processed 500/50000 URLs...`
- Creates checkpoint file: `output/large-site.com/checkpoint.json`
- Resumes if interrupted

### Adjustment:

**Constraints & Refinements:**

1. **Rate Limiting Implementation**:
   - Use `time.sleep()` between requests
   - Implement exponential backoff: `delay = base_delay * (2 ** retry_count)`
   - Max retries: 3
   - Respect `Retry-After` HTTP header if present

2. **Memory Efficiency**:
   - Use `xml.etree.ElementTree.iterparse()` with `clear()` on elements after processing
   - Never load entire URL list into memory
   - Write markdown line-by-line to file

3. **Sitemap Discovery Logic**:

   ```python
   def discover_sitemap(base_url: str) -> str:
       # Try direct sitemap.xml
       # Try sitemap_index.xml
       # Parse robots.txt for Sitemap directive
       # Return first valid sitemap URL
   ```

4. **Checkpointing**:
   - Save progress to `checkpoint.json` in output directory
   - Format: `{"processed_count": 1000, "last_url": "...", "timestamp": "..."}`
   - On restart: load checkpoint and resume from last position

5. **Error Recovery**:
   - Skip malformed XML entries, log to stderr
   - Continue processing after network errors
   - Only fail if no URLs can be extracted

6. **Output Contract**:
   - **Success**: JSON with `status: "success"`, `data` object containing:
     - `markdown`: Full markdown content
     - `url`: Original input URL
     - `sitemap_url`: Discovered sitemap URL
     - `total_urls`: Count of extracted URLs
     - `saved_to`: Absolute path to output file
   - **Error**: JSON with `status: "error"`, `error` string

7. **File Organization**:
   - Follow [`url_to_markdown.py:93-100`](skills-repository/url_to_markdown/url_to_markdown.py:93-100) pattern
   - Create `output/<domain>/` directory
   - Sanitize domain names (replace special chars with underscores)
   - Use `os.makedirs(output_dir, exist_ok=True)`

8. **Logging**:
   - All logs to stderr (not stdout)
   - Format: `[LOG] <message>`
   - Include progress updates every 100 URLs
   - Log rate limit events: `[LOG] Rate limit hit, backing off for 2s`

### Type of Output:

**Deliverables:**

1. **Skill Directory Structure**:

   ```
   skills-repository/sitemap_to_markdown/
   ├── SKILL.md
   ├── output/
   │   └── .gitignore  # Ignore generated files
   └── sitemap_to_markdown.py
   ```

2. **SKILL.md** following [`url_to_markdown/SKILL.md`](skills-repository/url_to_markdown/SKILL.md) format:
   - YAML frontmatter with `name`, `description`, `schema_source`
   - Description section
   - Usage section with discovery and execution examples
   - Executable path

3. **sitemap_to_markdown.py** with:
   - Pydantic InputModel and OutputModel
   - Typer CLI with all required options
   - Schema discovery mode
   - Sitemap discovery logic
   - XML streaming parser
   - Rate limiting with exponential backoff
   - Batch processing
   - Checkpointing
   - Markdown generation with hierarchical grouping
   - Error handling with structured JSON responses
   - Automatic output directory creation
   - UTF-8 encoding for all file operations

4. **Output Format**:
   - Markdown file with hierarchical URL organization
   - JSON response to stdout (for agent consumption)
   - Logs to stderr (for debugging)

**Success Criteria:**

- ✅ Skill follows Agent Skills specification
- ✅ Handles sitemaps with 50K+ URLs without memory issues
- ✅ Implements rate limiting (1 request/second default)
- ✅ Processes sitemap indexes (multi-sitemap sites)
- ✅ Resumes from checkpoint if interrupted
- ✅ Returns structured JSON responses
- ✅ Follows existing code conventions (Typer, Pydantic, UTF-8)
- ✅ Provides clear progress feedback
- ✅ Handles network errors gracefully

### Extras:

**Additional Context:**

**Sitemap Protocol Reference:**

- Single sitemap: `<urlset><url><loc>...</loc></url></urlset>`
- Sitemap index: `<sitemapindex><sitemap><loc>...</loc></sitemap></sitemapindex>`
- Optional elements: `<lastmod>`, `<changefreq>`, `<priority>`

**XML Namespaces:**

- Sitemaps use `xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"`

**Rate Limiting Best Practices:**

- Start with conservative rate (1 req/sec)
- Increase gradually if no 429 responses
- Implement jitter to avoid thundering herd
- Log all rate limit events

**Memory Optimization Techniques:**

```python
# Instead of:
urls = []
for url in root.findall('.//{ns}loc'):
    urls.append(url.text)

# Use:
for url in root.iterfind('.//{ns}loc'):
    process_url(url.text)
    url.clear()  # Free memory
```

**Progress Reporting Pattern:**

```python
if processed_count % 100 == 0:
    print(f"[LOG] Processed {processed_count}/{total_urls} URLs...", file=sys.stderr)
```

**Testing Considerations:**

- Test with small sitemap (< 100 URLs)
- Test with large sitemap (> 50K URLs)
- Test with sitemap index
- Test rate limiting (simulate 429 responses)
- Test interruption and resume
- Test malformed XML handling

**Related Skills:**

- [`url_to_markdown`](skills-repository/url_to_markdown/url_to_markdown.py) - Baseline for HTTP requests, output organization
- [`path_ref_updater`](skills-repository/path_ref_updater/path_ref_updater.py) - Reference for structured error handling

**Documentation:**

- Include inline docstrings for all functions
- Add type hints for all parameters
- Document rate limiting behavior in SKILL.md
- Provide examples for common use cases

---

## Usage Instructions

1. **Copy "Optimized Prompt" section** above
2. **Provide to next agent** (Code mode or Architect mode)
3. **Reference Analysis Summary** for constraint rationale:
   - Rate limiting patterns from existing codebase
   - Memory optimization requirements
   - Output format conventions
   - Error handling patterns
4. **Re-run RAPO** with refined input for iterations if needed

**Implementation Order:**

1. Create skill directory structure
2. Implement SKILL.md with frontmatter
3. Create sitemap_to_markdown.py with Pydantic models
4. Implement sitemap discovery logic
5. Add XML streaming parser
6. Implement rate limiting
7. Add batch processing and checkpointing
8. Generate markdown output
9. Add error handling and logging
10. Test with small and large sitemaps

**Validation Checklist:**

- [ ] Skill follows Agent Skills specification
- [ ] Schema discovery works (`--schema` flag)
- [ ] Sitemap discovery handles all cases
- [ ] Rate limiting implemented with backoff
- [ ] Large sitemaps processed without memory issues
- [ ] Checkpointing works on interruption
- [ ] Output format matches specification
- [ ] Error handling returns structured JSON
- [ ] UTF-8 encoding used throughout
- [ ] Logs to stderr, JSON to stdout

_Generated by RAPO on 2026-01-03 19:01:52 UTC_
