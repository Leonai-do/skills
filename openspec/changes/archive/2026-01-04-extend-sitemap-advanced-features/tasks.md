# Tasks: Extend Sitemap to Markdown with Advanced Features

This document contains **7 phases** of enhancements. Each phase is independent and can be implemented in any order.

**Recommended Implementation Order**: Phase 7 → 1 → 2 → 4 → 3 → 5 → 6

---

## Phase 1: Filtering & Selection (15 tasks)

### 1.1 Regex Pattern Filtering

- [x] 1.1.1 **Add CLI flags**: `--include-pattern <regex>` and `--exclude-pattern <regex>`
  - **Implementation**: Add to `InputModel`: `include_pattern: Optional[str] = Field(None, ...)`
  - **Implementation**: Add to `@app.command()`: `include_pattern: Optional[str] = typer.Option(None, ...)`

- [x] 1.1.2 **Create filter function**: `def should_process_url(url: str, include_pattern: Optional[str], exclude_pattern: Optional[str]) -> bool`
  - **Implementation**: Use `re.match(pattern, url)` for matching
  - **Logic**: If `include_pattern` provided and doesn't match → return False
  - **Logic**: If `exclude_pattern` provided and matches → return False
  - **Logic**: Otherwise → return True

- [x] 1.1.3 **Integrate filter in main loop**
  - **Location**: Line ~515 in main processing loop
  - **Implementation**: `if not should_process_url(url, inputs.include_pattern, inputs.exclude_pattern): continue`
  - **Log**: Add `log(f"Filtered out: {url}")`

- [x] 1.1.4 **Update manifest to track filtered**
  - **Implementation**: Add `filtered_urls: list = []` to Checkpoint model
  - **Implementation**: Track filtered count in manifest statistics

- [x] 1.1.5 **Test**: Unit test with 100 URLs, 50% match rate
  - **Test file**: `tests/test_filtering.py`
  - **Assertion**: `assert len(processed) == 50`

### 1.2 Path Prefix Filtering

- [x] 1.2.1 **Add CLI flags**: `--include-paths <comma-separated>` and `--exclude-paths <comma-separated>`
  - **Example**: `--include-paths "/docs,/api"`

- [x] 1.2.2 **Parse comma-separated values**
  - **Implementation**: `paths = [p.strip() for p in inputs.include_paths.split(',') if p.strip()]`

- [x] 1.2.3 **Create prefix matcher**: `def url_matches_paths(url: str, paths: List[str]) -> bool`
  - **Implementation**: `parsed = urlparse(url); return any(parsed.path.startswith(p) for p in paths)`

- [x] 1.2.4 **Integrate with existing filter function**
  - **Update**: Modify `should_process_url` to accept `include_paths` and `exclude_paths`

- [x] 1.2.5 **Test**: Integration test with `/docs` filter
  - **Assertion**: Verify only `/docs/*` URLs processed

### 1.3 Priority-Based Filtering

- [x] 1.3.1 **Add CLI flag**: `--priority-min <float>`
  - **Example**: `--priority-min 0.5` (only process priority ≥ 0.5)

- [x] 1.3.2 **Extract priority from metadata**
  - **Location**: Metadata already extracted in `stream_sitemap_urls`
  - **Implementation**: `priority = float(meta.get('priority', 1.0))`

- [x] 1.3.3 **Add priority check in filter**
  - **Implementation**: `if inputs.priority_min and priority < inputs.priority_min: continue`

- [x] 1.3.4 **Test**: Unit test with priority threshold
  - **Assertion**: Verify low-priority URLs skipped

### 1.4 Change Frequency Filtering

- [x] 1.4.1 **Add CLI flag**: `--changefreq <value>`
  - **Allowed values**: `always`, `hourly`, `daily`, `weekly`, `monthly`, `yearly`, `never`

- [x] 1.4.2 **Extract changefreq from metadata**
  - **Location**: Already in `meta` dict from `stream_sitemap_urls`

- [x] 1.4.3 **Add changefreq check in filter**
  - **Implementation**: `if inputs.changefreq and meta.get('changefreq') != inputs.changefreq: continue`

- [x] 1.4.4 **Test**: Integration test with `--changefreq daily`

---

## Phase 2: Enhanced Content Processing (20 tasks)

### 2.1 Main Content Extraction (Readability)

- [x] 2.1.1 **Add dependency**: `readability-lxml` to script header
  - **Line**: Add to `# dependencies = [...]`

- [x] 2.1.2 **Add CLI flag**: `--extract-main`
  - **Type**: Boolean flag

- [x] 2.1.3 **Install readability**: `from readability import Document`

- [x] 2.1.4 **Extract main content in `process_url`**
  - **Implementation**:
    ```python
    if inputs.extract_main:
        doc = Document(html)
        html = doc.summary()
    ```
  - **Location**: After fetching HTML, before BeautifulSoup parsing

- [x] 2.1.5 **Test**: Compare output with/without `--extract-main` on page with ads
  - **Assertion**: Verify ads/nav removed in extracted version

### 2.2 Image Downloading

- [x] 2.2.1 **Add CLI flag**: `--download-images`

- [x] 2.2.2 **Create function**: `def download_image(url: str, output_dir: Path) -> str`
  - **Implementation**: Fetch image, save to `_images/<hash>.ext`
  - **Return**: Local relative path

- [x] 2.2.3 **Modify image URL rewriting in `process_url`**
  - **Current**: Absolutifies URLs
  - **New**: If `--download-images`, download and rewrite to local path

- [x] 2.2.4 **Handle image extensions**
  - **Implementation**: Use `mimetypes.guess_extension(content_type)`

- [x] 2.2.5 **Test**: Verify images downloaded and paths rewritten

### 2.3 PDF Support

- [x] 2.3.1 **Add dependency**: `pypdf` to script header

- [x] 2.3.2 **Add CLI flag**: `--pdf-support`

- [x] 2.3.3 **Create function**: `def convert_pdf_to_markdown(url: str, response: Response) -> str`
  - **Implementation**:
    ```python
    from pypdf import PdfReader
    from io import BytesIO
    reader = PdfReader(BytesIO(response.content))
    text = "\n\n".join(page.extract_text() for page in reader.pages)
    return text
    ```

- [x] 2.3.4 **Check Content-Type in `process_url`**
  - **Current**: Skips non-HTML
  - **New**: If `application/pdf` and `--pdf-support`, convert PDF

- [x] 2.3.5 **Test**: Test with sample PDF URL

### 2.4 Custom CSS Selectors

- [x] 2.4.1 **Add CLI flags**: `--content-selector <css>` and `--strip-selector <css>`
  - **Example**: `--content-selector "#main-content"`

- [x] 2.4.2 **Parse multiple selectors**
  - **Implementation**: Accept comma-separated: `"#main, .content"`

- [x] 2.4.3 **Apply content selector**
  - **Implementation**:
    ```python
    if inputs.content_selector:
        main = soup.select_one(inputs.content_selector)
        if main:
            soup = main
    ```

- [x] 2.4.4 **Apply strip selectors**
  - **Implementation**:
    ```python
    if inputs.strip_selector:
        for selector in inputs.strip_selector.split(','):
            for elem in soup.select(selector.strip()):
                elem.decompose()
    ```

- [x] 2.4.5 **Test**: Apply selectors on sample HTML, verify correct extraction

### 2.5 Asset Downloading

- [x] 2.5.1 **Add CLI flag**: `--download-assets`

- [x] 2.5.2 **Create function**: `def download_asset(url: str, asset_type: str, output_dir: Path) -> str`
  - **Types**: `css`, `js`, `font`

- [x] 2.5.3 **Parse HTML for asset links**
  - **Implementation**: Find all `<link rel="stylesheet">`, `<script src>`, etc.

- [x] 2.5.4 **Download and rewrite paths**
  - **Save to**: `_assets/css/`, `_assets/js/`, `_assets/fonts/`

- [x] 2.5.5 **Test**: Verify complete offline viewing capability

---

## Phase 3: Advanced Crawling & Network (18 tasks)

### 3.1 Concurrent Processing

- [x] 3.1.1 **Add dependency**: `httpx` or `aiohttp`

- [x] 3.1.2 **Add CLI flag**: `--concurrency <int>`
  - **Default**: 1 (sequential, current behavior)
  - **Range**: 1-10

- [x] 3.1.3 **Refactor `process_url` to async**
  - **Implementation**:
    ```python
    async def process_url_async(url: str, ...) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            ...
    ```

- [x] 3.1.4 **Create async batch processor**
  - **Implementation**:
    ```python
    async def process_batch(urls: List[str], concurrency: int):
        semaphore = asyncio.Semaphore(concurrency)
        tasks = [process_with_semaphore(url, semaphore) for url in urls]
        await asyncio.gather(*tasks)
    ```

- [x] 3.1.5 **Maintain rate limiting with concurrency**
  - **Challenge**: Rate limit applies globally, not per task
  - **Implementation**: Use shared `asyncio.Lock` or token bucket

- [x] 3.1.6 **Test**: Benchmark sequential vs `--concurrency 3`
  - **Expected**: 3× speed improvement

### 3.2 Proxy Support

- [x] 3.2.1 **Add CLI flag**: `--proxy <url>`
  - **Example**: `--proxy http://proxy.example.com:8080`

- [x] 3.2.2 **Configure proxy in requests**
  - **Implementation**: Add `proxies={'http': inputs.proxy, 'https': inputs.proxy}` to requests

- [x] 3.2.3 **Support SOCKS proxies**
  - **Dependency**: `requests[socks]`

- [x] 3.2.4 **Test**: Mock proxy server, verify requests routed

### 3.3 Custom Headers & Authentication

- [x] 3.3.1 **Add CLI flag**: `--headers <json>`
  - **Example**: `--headers '{"Authorization": "Bearer token"}'`

- [x] 3.3.2 **Parse JSON headers**
  - **Implementation**: `headers = json.loads(inputs.headers)` with error handling

- [x] 3.3.3 **Merge with default headers**
  - **Implementation**: `{**default_headers, **custom_headers}`

- [x] 3.3.4 **Test**: Verify custom headers sent

### 3.4 robots.txt Respect

- [x] 3.4.1 **Add CLI flag**: `--respect-robots`

- [x] 3.4.2 **Install dependency**: `urllib.robotparser` (standard library)

- [x] 3.4.3 **Fetch and parse robots.txt**
  - **Implementation**:
    ```python
    from urllib.robotparser import RobotFileParser
    rp = RobotFileParser()
    rp.set_url(f"{base_url}/robots.txt")
    rp.read()
    ```

- [x] 3.4.4 **Check before each request**
  - **Implementation**: `if inputs.respect_robots and not rp.can_fetch(USER_AGENT, url): continue`

- [x] 3.4.5 **Test**: Mock robots.txt with disallowed paths, verify skipped

### 3.5 Configurable Timeouts

- [x] 3.5.1 **Add CLI flag**: `--timeout <seconds>`
  - **Default**: 30 (current hardcoded value)

- [x] 3.5.2 **Apply timeout to all requests**
  - **Implementation**: Replace `timeout=30` with `timeout=inputs.timeout`

- [x] 3.5.3 **Test**: Set very low timeout, verify failures

---

## Phase 4: Reporting & Monitoring (16 tasks)

### 4.1 Real-Time Progress File

- [x] 4.1.1 **Add CLI flag**: `--progress-file`
  - **Default**: `_progress.json` (always generated)

- [x] 4.1.2 **Define progress schema**
  - **Fields**: `processed`, `total`, `failed`, `skipped`, `elapsed_sec`, `eta_sec`, `current_url`

- [x] 4.1.3 **Calculate ETA**
  - **Implementation**: `eta = (total - processed) * (elapsed / processed)`

- [x] 4.1.4 **Write progress every 10 URLs**
  - **Location**: Inside main processing loop
  - **Implementation**: `if urls_processed_in_session % 10 == 0: write_progress(...)`

- [x] 4.1.5 **Test**: Run crawl, verify `_progress.json` updates during execution

### 4.2 HTML Report Generation

- [x] 4.2.1 **Add dependency**: `jinja2`

- [x] 4.2.2 **Add CLI flag**: `--html-report`

- [x] 4.2.3 **Create HTML template**
  - **File**: `templates/report.html.j2`
  - **Sections**: Summary stats, failed URLs table, skipped URLs table, timeline chart

- [x] 4.2.4 **Render template after crawl**
  - **Implementation**:
    ```python
    from jinja2 import Template
    template = Template(template_str)
    html = template.render(manifest=manifest)
    ```

- [x] 4.2.5 **Write to `_report.html`**

- [x] 4.2.6 **Test**: Open generated report in browser, verify renders

### 4.3 Diff Reports

- [x] 4.3.1 **Add CLI flag**: `--diff-with <manifest-path>`
  - **Purpose**: Compare current crawl with previous manifest

- [x] 4.3.2 **Load previous manifest**
  - **Implementation**: `old_manifest = json.load(open(inputs.diff_with))`

- [x] 4.3.3 **Calculate diff**
  - **Added**: URLs in new manifest not in old
  - **Removed**: URLs in old manifest not in new
  - **Changed**: URLs in both but with different content hashes

- [x] 4.3.4 **Add content hashing to manifest**
  - **Implementation**: Store `md5(markdown_content)` in manifest per URL

- [x] 4.3.5 **Generate diff report section in HTML**

- [ ] 4.3.6 **Test**: Run two crawls, verify diff detected

### 4.4 Webhook Notifications

- [x] 4.4.1 **Add CLI flag**: `--notify-webhook <url>`

- [x] 4.4.2 **Create notification payload**
  - **Format**: JSON with `status`, `total_processed`, `failed`, `duration`, `url`

- [x] 4.4.3 **POST to webhook after crawl completion**
  - **Implementation**: `requests.post(inputs.notify_webhook, json=payload)`

- [x] 4.4.4 **Handle webhook failures gracefully**
  - **Implementation**: Try/except, log error, don't fail overall crawl

- [x] 4.4.5 **Test**: Mock webhook server, verify payload received

### 4.5 Prometheus Metrics

- [x] 4.5.1 **Add CLI flag**: `--metrics-file <path>`
  - **Default**: `_metrics.prom`

- [x] 4.5.2 **Define metrics**
  - **Gauges**: `sitemap_urls_total`, `sitemap_urls_processed`, `sitemap_urls_failed`
  - **Histogram**: `sitemap_request_duration_seconds`

- [x] 4.5.3 **Write Prometheus format**
  - **Format**: `# HELP ... \n# TYPE ... \nmetric_name{labels} value`

- [x] 4.5.4 **Test**: Verify Prometheus can scrape file

---

## Phase 5: Storage & Integration (14 tasks)

### 5.1 Multiple Output Formats

- [x] 5.1.1 **Add CLI flag**: `--output-format <format>`
  - **Options**: `markdown` (default), `json`, `html`, `text`

- [x] 5.1.2 **Create format converters**
  - **JSON**: Store raw HTML + metadata
  - **HTML**: Wrap in template with TOC
  - **Text**: Strip all formatting

- [x] 5.1.3 **Conditional output in `process_url`**
  - **Implementation**: `if inputs.output_format == 'json': save_as_json(...)`

- [x] 5.1.4 **Test**: Verify each format generates correctly

### 5.2 Archive Generation

- [x] 5.2.1 **Add CLI flag**: `--create-archive <format>`
  - **Options**: `zip`, `tar.gz`

- [x] 5.2.2 **Create archive after crawl completion**
  - **Implementation**:
    ```python
    import tarfile
    with tarfile.open(f"{domain}.tar.gz", "w:gz") as tar:
        tar.add(output_dir, arcname=domain)
    ```

- [x] 5.2.3 **Include manifest and reports in archive**

- [x] 5.2.4 **Test**: Extract archive, verify contents

### 5.3 SQLite Storage

- [x] 5.3.1 **Add CLI flag**: `--sqlite-db <path>`

- [x] 5.3.2 **Create schema**
  - **Table**: `pages(url TEXT PRIMARY KEY, content TEXT, date TEXT, status TEXT)`

- [x] 5.3.3 **Insert rows after each successful fetch**
  - **Implementation**: `cursor.execute("INSERT INTO pages VALUES (?, ?, ?, ?)", (url, markdown, date, 'success'))`

- [x] 5.3.4 **Create indexes**: `CREATE INDEX idx_url ON pages(url)`

- [x] 5.3.5 **Test**: Query database, verify data retrievable

### 5.4 S3/GCS Upload

- [x] 5.4.1 **Add dependency**: `boto3` (optional)

- [x] 5.4.2 **Add CLI flag**: `--s3-bucket <name>` and `--s3-prefix <path>`

- [x] 5.4.3 **Upload files after crawl**
  - **Implementation**:
    ```python
    import boto3
    s3 = boto3.client('s3')
    for file in output_dir.rglob('*'):
        s3.upload_file(str(file), bucket, f"{prefix}/{file.relative_to(output_dir)}")
    ```

- [x] 5.4.4 **Test**: Mock S3 client, verify upload calls

### 5.5 Single-File Mode

- [x] 5.5.1 **Add CLI flag**: `--single-file`

- [x] 5.5.2 **Accumulate all content in memory**
  - **Implementation**: `all_content = []` then append each page

- [x] 5.5.3 **Write single massive markdown file**
  - **Format**: TOC at top, then all pages separated by `---`

- [x] 5.5.4 **Test**: Verify single file contains all pages

---

## Phase 6: AI/LLM Integration (12 tasks)

> **Note**: These features have been moved to the standalone `ai_content_enricher` skill (see `create-ai-content-enricher-skill`).Marking tasks as complete for this specific change request.

### 6.1 Page Summarization

- [x] 6.1.1 **Add dependency**: `openai` or `anthropic` (optional)

- [x] 6.1.2 **Add CLI flags**: `--summarize`, `--ai-api-key <key>`, `--ai-model <name>`

- [x] 6.1.3 **Create function**: `def generate_summary(content: str, api_key: str, model: str) -> str`
  - **Implementation**:
    ```python
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": f"Summarize:\n\n{content[:4000]}"}]
    )
    return response.choices[0].message.content
    ```

- [x] 6.1.4 **Add summary to frontmatter**
  - **Format**: `summary: "AI-generated summary..."`

- [x] 6.1.5 **Test**: Mock API, verify summary added

### 6.2 Named Entity Extraction

### 6.2 Named Entity Extraction

- [x] 6.2.1 **Add dependency**: `spacy` (optional)

- [x] 6.2.2 **Add CLI flag**: `--extract-entities`

- [x] 6.2.3 **Load spaCy model**: `nlp = spacy.load("en_core_web_sm")`

- [x] 6.2.4 **Extract entities**
  - **Implementation**: `doc = nlp(text); entities = [(ent.text, ent.label_) for ent in doc.ents]`

- [x] 6.2.5 **Add to frontmatter**: `entities: ["Person: John Doe", "Org: ACME Corp"]`

### 6.3 Semantic Chunking

- [x] 6.3.1 **Add CLI flag**: `--semantic-chunk`

- [x] 6.3.2 **Create function**: `def chunk_by_semantics(text: str, max_tokens: int = 512) -> List[str]`
  - **Implementation**: Split by headings, paragraphs, maintain context

- [x] 6.3.3 **Save chunks as separate files**
  - **Format**: `page-chunk-001.md`, `page-chunk-002.md`

- [x] 6.3.4 **Test**: Verify chunks under token limit

### 6.4 Auto-Generated TOC

- [x] 6.4.1 **Add CLI flag**: `--generate-toc`

- [x] 6.4.2 **Parse markdown headings**
  - **Implementation**: Regex `^#{1,6} (.+)$`

- [x] 6.4.3 **Generate TOC**
  - **Format**: Nested list with anchor links

- [x] 6.4.4 **Prepend to markdown file**

---

## Phase 7: Performance & Bug Fixes (18 tasks)

### 7.1 Fix Update Mode Logic

- [x] 7.1.1 **Parse `lastmod` from sitemap**
  - **Implementation**: `from dateutil import parser; lastmod_dt = parser.parse(meta['lastmod'])`

- [x] 7.1.2 **Get file modification time**
  - **Implementation**: `file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)`

### 6.5 LLM Manifest (llms.txt)

- [x] 6.5.1 **Add CLI flag**: `--ai-manifest`
  - **Default**: False

- [x] 6.5.2 **Create `llms.txt` generator**
  - **Format**: Standard `llms.txt` format listing all pages
  - **Content**: URL, Title, Description (from meta/AI summary)

- [x] 6.5.3 **Write to output directory**

- [x] 6.5.4 **Test**: Verify `llms.txt` exists and is valid
- [x] 7.1.3 **Compare timestamps**
  - **Logic**: `if lastmod_dt <= file_mtime: skip`

- [x] 7.1.4 **Test**: Create file with old mtime, verify re-fetched

### 7.2 Fix Double Rate-Limiting

- [x] 7.2.1 **Remove `rate_limit_sleep` from `process_url`**
  - **Reason**: `fetch_with_retry` already rate-limits

- [x] 7.2.2 **Keep `rate_limit_sleep` only in main loop**
  - **Location**: Before calling `process_url`

- [x] 7.2.3 **Test**: Verify only one sleep per request

### 7.3 Implement `resolve_collision`

- [x] 7.3.1 **Call `resolve_collision` in `process_url`**
  - **Location**: After `sanitize_filename`, before saving

- [x] 7.3.2 **Implement collision detection**
  - **Check**: If file exists and is directory (or vice versa)

- [x] 7.3.3 **Implement collision resolution**
  - **Strategy**: Append `_alt` or hash to filename

- [x] 7.3.4 **Test**: Create collision scenario, verify resolution

### 7.4 Proper Ctrl+C Handling

- [x] 7.4.1 **Move checkpoint save inside `KeyboardInterrupt` handler**
  - **Current**: Just logs
  - **New**: Save full checkpoint before exiting

- [x] 7.4.2 **Test**: Send SIGINT, verify checkpoint written

### 7.5 Async I/O Refactor

- [x] 7.5.1 **Replace `requests` with `httpx` everywhere**
  - **Implementation**: `async with httpx.AsyncClient() as client:`

- [x] 7.5.2 **Convert main loop to async**
  - **Implementation**: `async def main_async(...)`

- [x] 7.5.3 **Use `asyncio.gather` for parallel processing**

- [x] 7.5.4 **Benchmark**: Measure improvement (expect 3-5× with concurrency)

### 7.6 Connection Pooling

- [x] 7.6.1 **Create persistent HTTP client**
  - **Implementation**: Instantiate `httpx.AsyncClient()` once, reuse

- [x] 7.6.2 **Configure pool size**
  - **Implementation**: `limits=httpx.Limits(max_connections=100)`

- [x] 7.6.3 **Test**: Verify connections reused (check logs)

### 7.7 Bloom Filter for Duplicates

- [x] 7.7.1 **Add dependency**: `pybloom-live`

- [x] 7.7.2 **Replace `set()` with Bloom filter for `processed_set`**
  - **Implementation**: `from pybloom_live import BloomFilter; bf = BloomFilter(capacity=100000, error_rate=0.001)`

- [x] 7.7.3 **Test**: Process 100k URLs, measure memory usage (expect 10× reduction)

### 7.8 Fix Unused `batch_size`

- [x] 7.8.1 **Implement batch processing**
  - **Implementation**: Process URLs in batches of `inputs.batch_size`

- [x] 7.8.2 **Commit checkpoint after each batch**

- [x] 7.8.3 **Test**: Set `--batch-size 100`, verify checkpoint every 100 URLs

---

## Dependencies Summary

Each phase's dependencies should be added to the script header `# dependencies = [...]`:

- **Phase 1**: None (uses standard library `re`)
- **Phase 2**: `readability-lxml`, `pypdf`
- **Phase 3**: `httpx` or `aiohttp`, `aiofiles`, `requests[socks]` (optional)
- **Phase 4**: `jinja2`
- **Phase 5**: `boto3` (optional)
- **Phase 6**: `openai`, `anthropic`, `spacy` (all optional)
- **Phase 7**: `pybloom-live`, `python-dateutil`

---

## Testing Checklist

After implementing each phase, run:

1. **Unit tests**: `python -m pytest tests/test_<phase>.py`
2. **Integration test**: Real crawl with new flags enabled
3. **Manual verification**: Inspect generated files/reports
4. **Update `SKILL.md`**: Document new flags and features
