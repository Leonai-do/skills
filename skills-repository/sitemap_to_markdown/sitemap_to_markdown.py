#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "pydantic",
#     "httpx",
#     "aiofiles",
#     "html2text",
#     "beautifulsoup4",
#     "python-dateutil",
#     "pybloom-live",
#     "readability-lxml",
#     "pypdf",
#     "jinja2"
# ]
# ///

from urllib.robotparser import RobotFileParser



import sys
import json
import os
import re
import random
import time
import asyncio
import xml.etree.ElementTree as ET
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import hashlib
from urllib.parse import urlparse, unquote, urljoin
from typing import Optional, Iterator, Tuple, Dict, Any, Set, List
from pathlib import Path

import typer
from pydantic import BaseModel, Field
import httpx
import aiofiles
import html2text
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
import mimetypes
from io import BytesIO

# Phase 4 Imports
try:
    from jinja2 import Template
except ImportError:
    Template = None


# Phase 2 Imports
try:
    from readability import Document
except ImportError:
    Document = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from pybloom_live import BloomFilter
    HAS_BLOOM = True
except ImportError:
    HAS_BLOOM = False

# --- Constants ---
NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
USER_AGENT = "Mozilla/5.0 (compatible; SitemapToMarkdown/1.0; +https://github.com/LeonAI-DO/Agent-Skills)"
DEFAULT_RATE_LIMIT = 1.0  # requests per second
DEFAULT_BATCH_SIZE = 1000
MAX_RETRIES = 3
CHECKPOINT_INTERVAL = 100

# --- 1. Define Input Schema ---
class InputModel(BaseModel):
    url: str = Field(..., description="The base URL or direct sitemap URL to process")
    rate_limit: float = Field(DEFAULT_RATE_LIMIT, description="Requests per second (default: 1.0)")
    batch_size: int = Field(DEFAULT_BATCH_SIZE, description="URLs processed per batch (default: 1000)")
    update: bool = Field(False, description="Incremental update: only fetch new/changed pages")
    max_pages: int = Field(10000, description="Maximum number of pages to process (default: 10000)")
    concurrency: int = Field(5, description="Number of concurrent requests (default: 5)")
    # Phase 1: Filtering
    include_pattern: Optional[str] = Field(None, description="Regex pattern to include")
    exclude_pattern: Optional[str] = Field(None, description="Regex pattern to exclude")
    include_paths: Optional[str] = Field(None, description="Comma-separated paths to include")
    exclude_paths: Optional[str] = Field(None, description="Comma-separated paths to exclude")
    priority_min: Optional[float] = Field(None, description="Minimum priority included")
    changefreq: Optional[str] = Field(None, description="Change frequency to include")
    
    # Phase 2: Content Processing
    extract_main: bool = Field(False, description="Extract main content using readability")
    download_images: bool = Field(False, description="Download images locally")
    pdf_support: bool = Field(False, description="Convert PDFs to Markdown")
    content_selector: Optional[str] = Field(None, description="CSS selector for main content")
    strip_selector: Optional[str] = Field(None, description="CSS selectors to remove (comma-separated)")
    download_assets: bool = Field(False, description="Download CSS/JS assets")
    
    # Phase 3: Advanced Network
    proxy: Optional[str] = Field(None, description="Proxy URL (http/https/socks5)")
    headers: Optional[str] = Field(None, description="Custom headers as JSON string")
    respect_robots: bool = Field(False, description="Respect robots.txt rules")
    respect_robots: bool = Field(False, description="Respect robots.txt rules")
    timeout: int = Field(30, description="Request timeout in seconds")

    # Phase 4: Reporting & Monitoring
    progress_file: Optional[str] = Field("_progress.json", description="Real-time progress file")
    html_report: bool = Field(False, description="Generate HTML report")
    diff_with: Optional[str] = Field(None, description="Manifest path to diff against")
    notify_webhook: Optional[str] = Field(None, description="Webhook URL for notifications")
    metrics_file: Optional[str] = Field(None, description="Prometheus metrics file definition")


# --- 2. Define Output Schema ---
class OutputModel(BaseModel):
    status: str = Field(..., description="Status of execution: 'success' or 'error'")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data on success")
    error: Optional[str] = Field(None, description="Error message on failure")

# --- 3. Checkpoint Model ---
class Checkpoint(BaseModel):
    version: int = 2
    started_at: str
    last_updated: str
    source_url: str
    sitemap_type: str  # "single" or "index"
    processed_urls: list = []  # List[str]
    failed_urls: list = []     # List[str]
    skipped_urls: list = []    # List[str]
    total_processed: int = 0

app = typer.Typer()

# --- Utility Functions ---

def log(message: str):
    """Log to stderr for monitoring"""
    print(f"[LOG] {message}", file=sys.stderr)

def validate_output_path(path: str, base_dir: str) -> bool:
    """Validate path to prevent traversal attacks"""
    if ".." in path:
        return False
    try:
        resolved = Path(path).resolve()
        base = Path(base_dir).resolve()
        return resolved.is_relative_to(base)
    except (ValueError, OSError):
        return False

def sanitize_domain(domain: str) -> str:
    """Sanitize domain for safe filename usage"""
    return re.sub(r'[^a-zA-Z0-9.-]', '_', domain)

def should_process_url(url: str, meta: Dict[str, Any], inputs: InputModel) -> bool:
    """Apply Phase 1 filtering rules"""
    # 1.1 Regex
    if inputs.include_pattern and not re.search(inputs.include_pattern, url):
        return False
    if inputs.exclude_pattern and re.search(inputs.exclude_pattern, url):
        return False
        
    # 1.2 Paths
    parsed = urlparse(url)
    if inputs.include_paths:
        paths = [p.strip() for p in inputs.include_paths.split(',') if p.strip()]
        if not any(parsed.path.startswith(p) for p in paths):
            return False
            
    if inputs.exclude_paths:
        paths = [p.strip() for p in inputs.exclude_paths.split(',') if p.strip()]
        if any(parsed.path.startswith(p) for p in paths):
            return False
            
    # 1.3 Priority
    if inputs.priority_min is not None:
        p_str = meta.get('priority', '0.5')
        try:
            priority = float(p_str)
            if priority < inputs.priority_min:
                return False
        except ValueError:
            pass
            
    # 1.4 Changefreq
    if inputs.changefreq:
        cf = meta.get('changefreq', '').lower()
        if cf != inputs.changefreq.lower():
            return False
            
            
    return True

async def check_robots(client: httpx.AsyncClient, base_url: str, user_agent: str, target_url: str) -> bool:
    """Check if URL is allowed by robots.txt"""
    # Note: Optimization - cache the parser per domain if possible.
    # For now, we fetch robots.txt every time? No, that's bad.
    # We should cache it. Since we are processing one domain mostly:
    # We can pass a cached parser or dict.
    # But for a simple stateless function:
    robots_url = f"{base_url.rstrip('/')}/robots.txt"
    try:
        # We need to fetch it to parse it. 
        # Since we don't have a shared state easily available in this function signature...
        # We'll rely on the main function to do this check or cache it on the client/inputs?
        # Let's assume the main loop handles the fetching once and passes the parser or we do it efficiently.
        # Actually, standard library RobotFileParser is synchronous and needs to read data.
        pass
    except Exception:
        pass
    return True

async def download_asset(client: httpx.AsyncClient, url: str, output_dir: Path, subfolder: str) -> Optional[str]:
    """Download asset and return relative path"""
    try:
        # Simple fetch, maybe less retries needed for assets? using same for robustness
        response = await client.get(url, timeout=15.0, follow_redirects=True)
        if response.status_code != 200:
            return None
            
        # Determine filename
        parsed = urlparse(url)
        name = Path(parsed.path).name or "asset"
        if not Path(name).suffix:
            ext = mimetypes.guess_extension(response.headers.get('content-type', ''))
            if ext:
                name += ext
        
        # Hash to prevent collisions/duplicates
        digest = hashlib.md5(url.encode()).hexdigest()[:8]
        stem = Path(name).stem
        suffix = Path(name).suffix
        safe_name = f"{stem}_{digest}{suffix}"
        
        asset_dir = output_dir / "_assets" / subfolder
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        save_path = asset_dir / safe_name
        async with aiofiles.open(save_path, 'wb') as f:
            await f.write(response.content)
            
        # Return relative path from the markdown file's perspective? 
        # Actually usually relative to root of output.
        # Markdown files can be deep in subdirs.
        # We need to return path relative to output_dir, then fix it up in caller?
        # Let's return path relative to output_dir.
        return f"_assets/{subfolder}/{safe_name}"
    except Exception as e:
        log(f"Failed to download asset {url}: {e}")
        return None

def resolve_collision(base_path: Path, relative_path: Path) -> Path:
    """
    Resolve file system collisions.
    Ensure we don't try to create a file where a directory exists or vice-versa.
    Appends a hash if the exact path already exists as a different type.
    """
    full_path = base_path / relative_path
    
    # Check if a directory exists where we want a file
    if full_path.is_dir():
         # Collision: We want index.md but index.md is a dir? Unlikely with .md extension
         # But if we want `foo` and `foo` is dir
         stem = full_path.stem
         suffix = full_path.suffix
         digest = hashlib.md5(str(full_path).encode()).hexdigest()[:8]
         new_name = f"{stem}_alt_{digest}{suffix}"
         return Path(new_name)
         
    # Check if a file exists where we want a directory (handled by parents creation usually)
    # But here we are just returning the file path.
    # If any parent is a file, we have a problem.
    # e.g. base/foo is file, we want base/foo/bar.md
    
    current = relative_path.parent
    while current != Path('.'):
         check_path = base_path / current
         if check_path.exists() and not check_path.is_dir():
             # Collision: Parent is a file
             # We can't fix the parent, so we must rename our path?
             # This is tricky. simpler to just rename the current file to avoid that tree.
             # e.g. base/foo_conflict/bar.md
             digest = hashlib.md5(str(relative_path).encode()).hexdigest()[:8]
             return Path(f"{relative_path.stem}_{digest}{relative_path.suffix}")
         current = current.parent
         
    return relative_path

def sanitize_filename(url: str) -> Path:
    """
    Convert URL to safe relative path.
    """
    parsed = urlparse(url)
    path_str = unquote(parsed.path).strip('/')
    
    if not path_str:
        return Path("index.md")
        
    parts = path_str.split('/')
    safe_parts = []
    
    for part in parts:
        safe_part = re.sub(r'[<>:"/\\|?*]', '_', part)
        if len(safe_part) > 200:
            safe_part = safe_part[:200]
        safe_parts.append(safe_part)
    
    p = Path(*safe_parts)
    
    has_extension = bool(p.suffix)
    is_trailing_slash = url.endswith('/')
    
    if is_trailing_slash:
        p = p / "index.md"
    elif not has_extension:
        p = p.with_suffix(".md")
    
    if parsed.query or parsed.fragment:
        hash_input = f"{parsed.query}#{parsed.fragment}"
        digest = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        stem = p.stem
        suffix = p.suffix
        p = p.with_name(f"{stem}_{digest}{suffix}")
        
    return p

def exponential_backoff(retry_count: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate delay with exponential backoff + jitter"""
    delay = min(base_delay * (2 ** retry_count), max_delay)
    jitter = random.uniform(0, 1)
    return delay + jitter

async def rate_limit_sleep(rate_limit: float):
    """Sleep to enforce rate limit"""
    if rate_limit <= 0:
        return
    delay = 1.0 / rate_limit
    await asyncio.sleep(delay)

async def fetch_with_retry(client: httpx.AsyncClient, url: str, rate_limit: float, timeout_sec: int = 30) -> Optional[httpx.Response]:
    """Fetch URL with exponential backoff and retry logic using httpx"""
    for retry in range(MAX_RETRIES):
        try:
            # We assume external pacing, but here we handle 429 delays
            response = await client.get(url, timeout=timeout_sec, follow_redirects=True)
            
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        delay = float(retry_after)
                        log(f"Rate limit hit, Retry-After: {delay}s")
                    except ValueError:
                        delay = exponential_backoff(retry)
                else:
                    delay = exponential_backoff(retry)
                    log(f"Rate limit hit, backing off for {delay:.1f}s")
                await asyncio.sleep(delay)
                continue
            
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            if retry < max_retries - 1:
                delay = exponential_backoff(retry)
                # log(f"Request failed (attempt {retry+1}/{max_retries}): {e}. Retrying in {delay:.1f}s")
                await asyncio.sleep(delay)
            else:
                log(f"Request failed after {max_retries} attempts: {e} URL: {url}")
                return None
    return None

async def validate_sitemap(client: httpx.AsyncClient, url: str) -> bool:
    """Validate that URL points to a valid XML sitemap"""
    try:
        response = await client.head(url, timeout=10.0, follow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' in content_type or url.endswith('.xml'):
                return True
    except httpx.HTTPError:
        pass
    return False

async def discover_sitemap(client: httpx.AsyncClient, base_url: str) -> Optional[str]:
    """Discover sitemap URL with explicit priority order."""
    log(f"Discovering sitemap for {base_url}")
    
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    # Priority 1: Direct XML 
    if base_url.endswith('.xml'):
        if await validate_sitemap(client, base_url):
            log(f"Using direct XML URL: {base_url}")
            return base_url
    
    # Priority 2: Standard locations
    candidates = [
        f"{base}/sitemap.xml",
        f"{base}/sitemap_index.xml",
    ]
    
    for candidate in candidates:
        if await validate_sitemap(client, candidate):
            log(f"Found sitemap at: {candidate}")
            return candidate
            
    # Priority 3: robots.txt
    robots_url = f"{base}/robots.txt"
    try:
        response = await client.get(robots_url, timeout=10.0, follow_redirects=True)
        for line in response.text.splitlines():
            if line.lower().startswith('sitemap:'):
                sitemap_url = line.split(':', 1)[1].strip()
                if await validate_sitemap(client, sitemap_url):
                    log(f"Found sitemap in robots.txt: {sitemap_url}")
                    return sitemap_url
    except httpx.HTTPError:
        pass
        
    log("No sitemap found at any location")
    return None

def stream_sitemap_urls(xml_content: str) -> Iterator[Tuple[str, dict]]:
    """Memory-efficient sitemap parsing using iterparse."""
    try:
        from io import StringIO
        context = ET.iterparse(StringIO(xml_content), events=('end',))
        
        current_url = None
        current_meta = {}
        
        for event, elem in context:
            tag = elem.tag.replace(NS, '')
            
            if tag == 'loc':
                current_url = elem.text
            elif tag == 'lastmod':
                current_meta['lastmod'] = elem.text
            elif tag == 'changefreq':
                current_meta['changefreq'] = elem.text
            elif tag == 'priority':
                current_meta['priority'] = elem.text
            elif tag == 'url':
                if current_url:
                    yield (current_url, current_meta)
                current_url = None
                current_meta = {}
                elem.clear()
    except ET.ParseError as e:
        log(f"XML parsing error: {e}")

def extract_sitemap_index(xml_content: str) -> list:
    """Extract child sitemap URLs from sitemap index"""
    sitemaps = []
    try:
        from io import StringIO
        context = ET.iterparse(StringIO(xml_content), events=('end',))
        current_loc = None
        for event, elem in context:
            tag = elem.tag.replace(NS, '')
            if tag == 'loc':
                current_loc = elem.text
            elif tag == 'sitemap':
                if current_loc:
                    sitemaps.append(current_loc)
                current_loc = None
                elem.clear()
    except ET.ParseError as e:
        log(f"XML parsing error in sitemap index: {e}")
    return sitemaps

def convert_pdf_to_markdown(content: bytes) -> str:
    """Convert PDF bytes to Markdown text"""
    if not PdfReader:
        return "Error: pypdf not installed"
    try:
        reader = PdfReader(BytesIO(content))
        text = []
        for page in reader.pages:
            extract = page.extract_text()
            if extract:
                text.append(extract)
        return "\n\n".join(text)
    except Exception as e:
        return f"Error converting PDF: {e}"

async def process_url(client: httpx.AsyncClient, url: str, output_dir: Path, inputs: InputModel) -> str:
    """Fetch and convert URL to Markdown."""
    # We pass 'inputs' now to access flags
    response = await fetch_with_retry(client, url, 0, timeout_sec=inputs.timeout) # Rate limit handled by caller
    if not response:
        return "failed"
        
    content_type = response.headers.get('Content-Type', '').lower()
    
    # PDF Support
    if 'application/pdf' in content_type:
        if inputs.pdf_support and PdfReader:
            text = convert_pdf_to_markdown(response.content)
            rel_path = sanitize_filename(url)
            rel_path = rel_path.with_suffix('.md') # Ensure .md
            rel_path = resolve_collision(output_dir, rel_path)
            save_path = output_dir / rel_path
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            header = f"---\nurl: {url}\ntype: pdf\ndate: {datetime.now().isoformat()}\n---\n\n"
            async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
                await f.write(header + text)
            log(f"Saved PDF: {url} -> {rel_path}")
            return "success"
        else:
            return "skipped"

    if 'text/html' not in content_type:
        return "skipped"
        
    try:
        html = response.text
        
        # 2.1 Main Content Extraction (Readability)
        if inputs.extract_main and Document:
            try:
                doc = Document(html)
                html = doc.summary() # This returns HTML of the main content
            except Exception as e:
                log(f"Readability failed for {url}: {e}")
                
        soup = BeautifulSoup(html, 'html.parser')
        
        # 2.4 Custom Selectors (Strip)
        if inputs.strip_selector:
            for selector in inputs.strip_selector.split(','):
                if selector.strip():
                    for elem in soup.select(selector.strip()):
                        elem.decompose()
        
        # 2.4 Custom Selectors (Content)
        if inputs.content_selector:
            main = soup.select_one(inputs.content_selector)
            if main:
                soup = BeautifulSoup(str(main), 'html.parser') # Create new soup from selection
        elif not inputs.extract_main:
             # Default generic cleaning if not using readability or custom selector
            for tag in soup(['script', 'style', 'nav', 'footer', 'iframe', 'noscript']):
                tag.decompose()
        
        # 2.2 / 2.5 Asset/Image Downloading & Rewriting
        # We need to process tags
        tasks = []
        
        # Images
        if inputs.download_images:
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    abs_url = urljoin(url, src)
                    # We can't await easily inside loop if we want parallelism?
                    # For now linear or create list of tasks.
                    # Let's do it sequentially for simplicity or simple gather?
                    # Modifying soup in place after download.
                    asset_path = await download_asset(client, abs_url, output_dir, "images")
                    if asset_path:
                         # We need to make this path relative to the markdown file?
                         # The markdown file is at `rel_path`. 
                         # `asset_path` is relative to `output_dir`.
                         # We'll calculate this later or just use absolute/root relative.
                         # Markdown standard often expects relative to file.
                         img['src'] = asset_path
                         
        # Assets (CSS/JS)
        if inputs.download_assets:
            # CSS
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href')
                if href:
                    abs_url = urljoin(url, href)
                    asset_path = await download_asset(client, abs_url, output_dir, "css")
                    if asset_path:
                        link['href'] = asset_path
            # JS
            for script in soup.find_all('script', src=True):
                src = script.get('src')
                if src:
                    abs_url = urljoin(url, src)
                    asset_path = await download_asset(client, abs_url, output_dir, "js")
                    if asset_path:
                        script['src'] = asset_path

        # Absolutify remaining URLs (if not downloaded)
        for tag in soup.find_all(['a', 'img']):
            if tag.has_attr('href'):
                # Don't overwrite if we just rewrote it to local
                if not tag['href'].startswith('_assets/'):
                     tag['href'] = urljoin(url, tag['href'])
            if tag.has_attr('src'):
                if not tag['src'].startswith('_assets/'):
                    tag['src'] = urljoin(url, tag['src'])
                
        # Convert
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = False
        converter.body_width = 0
        converter.ul_item_mark = '-'
        markdown = converter.handle(str(soup))
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        rel_path = sanitize_filename(url)
        rel_path = resolve_collision(output_dir, rel_path)
        
        # Fixup asset paths to be relative to the markdown file
        # Current asset paths are `_assets/...`. Markdown file is `foo/bar.md`.
        # We need `../../_assets/...`
        # Simple string replace? Or robust path calculation?
        # Let's simple string replace `_assets/` with `rel_to_root/_assets/`
        depth = len(rel_path.parts) - 1
        if depth > 0:
            prefix = "../" * depth
            markdown = markdown.replace("_assets/", f"{prefix}_assets/")
            # Also need to fix up HTML attributes if we kept them? 
            # html2text keeps some attributes.
            
        save_path = output_dir / rel_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        header = f"---\nurl: {url}\ndate: {datetime.now().isoformat()}\n---\n\n"
        
        async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
            await f.write(header + markdown)
            
        log(f"Saved: {url} -> {rel_path}")
        return "success"
        
    except Exception as e:
        log(f"Conversion error for {url}: {e}")
        return "failed"

def save_checkpoint(checkpoint_path: str, checkpoint: Checkpoint):
    """Save checkpoint synchronously (safe since called infrequently or at exit)"""
    try:
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint.model_dump(), f, indent=2)
        log(f"Checkpoint saved: {checkpoint.total_processed} URLs processed")
    except Exception as e:
        log(f"Failed to save checkpoint: {e}")

def load_checkpoint(checkpoint_path: str) -> Optional[Checkpoint]:
    try:
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Checkpoint(**data)
    except Exception as e:
        log(f"Failed to load checkpoint: {e}")
    return None

# --- Phase 4 Reporting Implementation ---

class ProgressStats(BaseModel):
    processed: int
    total: int
    failed: int
    skipped: int
    elapsed_sec: float
    eta_sec: float
    current_url: str = ""

def write_progress(path: Path, stats: ProgressStats):
    try:
        with open(path, 'w') as f:
            json.dump(stats.model_dump(), f)
    except Exception:
        pass

def write_prometheus_metrics(path: Path, stats: ProgressStats):
     try:
        content = f"""# HELP sitemap_urls_total Total URLs to process
# TYPE sitemap_urls_total gauge
sitemap_urls_total {stats.total}
# HELP sitemap_urls_processed URLs processed successfully
# TYPE sitemap_urls_processed gauge
sitemap_urls_processed {stats.processed}
# HELP sitemap_urls_failed URLs failed
# TYPE sitemap_urls_failed gauge
sitemap_urls_failed {stats.failed}
# HELP sitemap_elapsed_seconds Elapsed time in seconds
# TYPE sitemap_elapsed_seconds gauge
sitemap_elapsed_seconds {stats.elapsed_sec}
"""
        with open(path, 'w') as f:
            f.write(content)
     except Exception:
         pass

def generate_html_report(output_dir: Path, manifest: Dict[str, Any]):
    if not Template:
        log("Jinja2 not installed, skipping HTML report")
        return
        
    template_str = """
<!DOCTYPE html>
<html>
<head>
    <title>Sitemap Crawl Report</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        .stats { display: flex; gap: 2rem; margin-bottom: 2rem; }
        .stat { border: 1px solid #ddd; padding: 1rem; border-radius: 4px; flex: 1; text-align: center; }
        .stat h3 { margin: 0 0 0.5rem; color: #666; font-size: 0.9rem; }
        .stat .value { font-size: 1.5rem; font-weight: bold; }
        h1 { border-bottom: 2px solid #eee; padding-bottom: 1rem; }
        .error { color: #d32f2f; }
    </style>
</head>
<body>
    <h1>Crawl Report: {{ manifest.source_url }}</h1>
    <div class="stats">
        <div class="stat">
            <h3>Total Processed</h3>
            <div class="value">{{ manifest.statistics.total_processed }}</div>
        </div>
        <div class="stat">
            <h3>Failed</h3>
            <div class="value error">{{ manifest.statistics.failed }}</div>
        </div>
        <div class="stat">
            <h3>Skipped</h3>
            <div class="value">{{ manifest.statistics.skipped }}</div>
        </div>
    </div>
    <p>Crawled on: {{ manifest.crawl_date }}</p>
    
    {% if manifest.failed_urls %}
    <h2>Failed URLs ({{ manifest.failed_urls|length }})</h2>
    <ul>
        {% for url in manifest.failed_urls %}
        <li>{{ url }}</li>
        {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
"""
    try:
        t = Template(template_str)
        html = t.render(manifest=manifest)
        with open(output_dir / "_report.html", "w") as f:
            f.write(html)
        log("HTML report generated")
    except Exception as e:
        log(f"Failed to generate HTML report: {e}")

async def send_webhook(url: str, payload: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload, timeout=10)
        except Exception as e:
            log(f"Webhook failed: {e}")

async def async_main(inputs: InputModel):

    log(f"Running sitemap_to_markdown (Async) with url: {inputs.url}")
    
    log(f"Running sitemap_to_markdown (Async) with url: {inputs.url}")
    
    # Setup HTTP client with connection pooling
    limits = httpx.Limits(max_keepalive_connections=100, max_connections=100)
    
    client_kwargs = {
        "headers": {"User-Agent": USER_AGENT},
        "limits": limits,
        "timeout": inputs.timeout
    }
    
    # 3.2 Proxy Support
    if inputs.proxy:
        client_kwargs['proxy'] = inputs.proxy
        
    # 3.3 Custom Headers
    if inputs.headers:
        try:
            custom_headers = json.loads(inputs.headers)
            client_kwargs['headers'].update(custom_headers)
        except json.JSONDecodeError:
            log("Error parsing custom headers JSON")

    async with httpx.AsyncClient(**client_kwargs) as client:
        
        # 3.4 robots.txt
        rp = None
        if inputs.respect_robots:
            parsed = urlparse(inputs.url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            robots_url = f"{base}/robots.txt"
            try:
                # We need to fetch robots.txt text first async
                r_resp = await client.get(robots_url, timeout=10)
                if r_resp.status_code == 200:
                    rp = RobotFileParser()
                    rp.parse(r_resp.text.splitlines())
                    log("Parsed robots.txt")
            except Exception as e:
                log(f"Failed to parse robots.txt: {e}")

        # 1. Discover
        sitemap_url = await discover_sitemap(client, inputs.url)
        if not sitemap_url:
            print(json.dumps(OutputModel(status="error", error="No sitemap found").model_dump()))
            return

        # 2. Setup output
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parsed = urlparse(inputs.url)
        domain = sanitize_domain(parsed.netloc)
        output_dir = Path(script_dir) / "output" / domain
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 3. Checkpoint & Bloom Filter
        checkpoint_path = output_dir / "checkpoint.json"
        checkpoint = load_checkpoint(str(checkpoint_path))
        
        if HAS_BLOOM:
            processed_set = BloomFilter(capacity=100000, error_rate=0.001)
        else:
            processed_set = set()
            
        failed_set = set()
        skipped_set = set()
        total_processed = 0
        total_processed = 0
        
        # Use simple utcnow replacement to avoid deprecation warning if possible
        def get_now_str():
            return datetime.now(timezone.utc).isoformat()
            
        start_time_dt = datetime.now(timezone.utc)
        start_time = start_time_dt.isoformat()
        
        if checkpoint:

            for u in checkpoint.processed_urls:
                processed_set.add(u)
            failed_set = set(checkpoint.failed_urls)
            skipped_set = set(checkpoint.skipped_urls)
            total_processed = checkpoint.total_processed
            start_time = checkpoint.started_at
            
        # 4. Fetch sitemap
        response = await fetch_with_retry(client, sitemap_url, inputs.rate_limit)
        if not response:
            print(json.dumps(OutputModel(status="error", error=f"Failed to fetch sitemap").model_dump()))
            return
            
        xml_content = response.text
        is_sitemap_index = '<sitemapindex' in xml_content.lower()
        
        urls_to_process = []
        if is_sitemap_index:
            child_sitemaps = extract_sitemap_index(xml_content)
            for child_url in child_sitemaps:
                child_res = await fetch_with_retry(client, child_url, inputs.rate_limit, timeout_sec=inputs.timeout)
                if child_res:
                    for url, meta in stream_sitemap_urls(child_res.text):
                        urls_to_process.append({'url': url, 'meta': meta})
        else:
            for url, meta in stream_sitemap_urls(xml_content):
                urls_to_process.append({'url': url, 'meta': meta})
                
        log(f"Found {len(urls_to_process)} URLs")
        
        log(f"Found {len(urls_to_process)} URLs")
        
        # 5. Process in Batches
        semaphore = asyncio.Semaphore(inputs.concurrency)
        total_urls_count = len(urls_to_process)
        
        async def worker(entry):
            nonlocal total_processed
            
            url = entry['url']
            meta = entry.get('meta', {})
            
            # Progress calculation helpers
            # Note: total_processed is updated atomically-ish in single thread loop mostly? 
            # In async code, 'total_processed += 1' is not atomic if await happens.
            # But here we invoke it.
            
            if url in processed_set:
                return

            # ... processing logic ...

            
            # Phase 1 Filtering
            if not should_process_url(url, meta, inputs):
                log(f"Filtered out: {url}")
                # We mark as skipped but also processed so we don't retry or anything
                skipped_set.add(url)
                processed_set.add(url)
                return
            
            # Phase 3 robots.txt check
            if rp and not rp.can_fetch(USER_AGENT, url):
                log(f"Blocked by robots.txt: {url}")
                skipped_set.add(url)
                processed_set.add(url)
                return

            # Update Mode Logic
            if inputs.update:
                rel_path = sanitize_filename(url)
                rel_path = resolve_collision(output_dir, rel_path)
                file_path = output_dir / rel_path
                
                if file_path.exists() and meta.get('lastmod'):
                    try:
                        lastmod_dt = date_parser.parse(meta['lastmod']).replace(tzinfo=None)
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if lastmod_dt <= file_mtime:
                            processed_set.add(url)
                            skipped_set.add(url)
                            return
                    except Exception:
                        pass
            
            async with semaphore:
                await rate_limit_sleep(inputs.rate_limit / inputs.concurrency) # Shared rate limit approx
                status = await process_url(client, url, output_dir, inputs)
                
            if status == "success":
                processed_set.add(url)
                total_processed += 1
            elif status == "failed":
                failed_set.add(url)
            elif status == "skipped":
                skipped_set.add(url)
                processed_set.add(url)
                
            # Phase 4.1: Progress reporting (approximate, every N items or time based?)
            # Doing it inside worker might be noisy. Better to do it after batch or periodically.
            # But let's do it here for "Real-Time".
            if total_processed % 10 == 0:
                elapsed = (datetime.now(timezone.utc) - start_time_dt).total_seconds()
                eta = 0
                if total_processed > 0:
                     avg_time = elapsed / total_processed
                     remaining = total_urls_count - total_processed
                     eta = remaining * avg_time
                
                stats = ProgressStats(
                    processed=total_processed,
                    total=total_urls_count,
                    failed=len(failed_set),
                    skipped=len(skipped_set),
                    elapsed_sec=elapsed,
                    eta_sec=eta,
                    current_url=url
                )
                if inputs.progress_file:
                     write_progress(output_dir / inputs.progress_file, stats)
                if inputs.metrics_file:
                     write_prometheus_metrics(output_dir / inputs.metrics_file, stats)

        # Batch processing
        batch_size = inputs.batch_size
        
        try:
            for i in range(0, len(urls_to_process), batch_size):

                if total_processed >= inputs.max_pages:
                    break
                    
                batch = urls_to_process[i:i+batch_size]
                await asyncio.gather(*[worker(entry) for entry in batch])
                
                # Checkpoint after batch
                cp = Checkpoint(
                    started_at=start_time,
                    last_updated=datetime.utcnow().isoformat(),
                    source_url=inputs.url,
                    sitemap_type="index" if is_sitemap_index else "single",
                    processed_urls=list(processed_set) if not HAS_BLOOM else [], # Bloom can't dump easily
                    failed_urls=list(failed_set),
                    skipped_urls=list(skipped_set),
                    total_processed=total_processed
                )
                save_checkpoint(str(checkpoint_path), cp)
                
        except asyncio.CancelledError:
             log("Cancelled - saving checkpoint")
             # logic in finally block?
             
        # Retry Failures
        if failed_set:
            log(f"Retrying {len(failed_set)} failures")
            retry_list = list(failed_set)
            failed_set.clear()
            # Simple retry without concurrency for safety? Or same worker
            for url in retry_list:
                # Re-use worker logic roughly... simplified here
                status = await process_url(client, url, output_dir, inputs)
                if status == "success":
                    processed_set.add(url)
                    total_processed += 1
                else:
                    failed_set.add(url)
                    
        # Finalize
        manifest = {
            "version": "1.0",
            "crawl_date": get_now_str(),
            "source_url": inputs.url,
            "statistics": {
                "total_processed": total_processed,
                "failed": len(failed_set),
                "skipped": len(skipped_set)
            },
            "failed_urls": list(failed_set),
            "skipped_urls": list(skipped_set)
        }
        
        manifest_path = output_dir / "_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        # Phase 4.2: HTML Report
        if inputs.html_report:
            generate_html_report(output_dir, manifest)
            
        # Phase 4.4: Webhook
        if inputs.notify_webhook:
             webhook_payload = {
                 "status": "completed",
                 "total_processed": total_processed,
                 "failed": len(failed_set),
                 "duration": (datetime.now(timezone.utc) - start_time_dt).total_seconds(),
                 "url": inputs.url
             }
             await send_webhook(inputs.notify_webhook, webhook_payload)
            
        result = {
            "url": inputs.url,
            "sitemap_url": sitemap_url,
            "total_processed": total_processed,
            "output_dir": str(output_dir)
        }
        print(json.dumps(OutputModel(status="success", data=result).model_dump()))

        
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)

@app.command()
def main(
    url: str = typer.Option(..., help="The URL"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
    rate_limit: float = typer.Option(DEFAULT_RATE_LIMIT),
    batch_size: int = typer.Option(DEFAULT_BATCH_SIZE),
    update: bool = typer.Option(False, "--update"),
    max_pages: int = typer.Option(10000),
    concurrency: int = typer.Option(5, "--concurrency"),
    # Phase 1
    include_pattern: Optional[str] = typer.Option(None, "--include-pattern", help="Regex to include"),
    exclude_pattern: Optional[str] = typer.Option(None, "--exclude-pattern", help="Regex to exclude"),
    include_paths: Optional[str] = typer.Option(None, "--include-paths", help="Comma-separated paths to include"),
    exclude_paths: Optional[str] = typer.Option(None, "--exclude-paths", help="Comma-separated paths to exclude"),
    priority_min: Optional[float] = typer.Option(None, "--priority-min", help="Min priority"),
    changefreq: Optional[str] = typer.Option(None, "--changefreq", help="Specific changefreq"),
    # Phase 2
    extract_main: bool = typer.Option(False, "--extract-main", help="Use Readability for main content"),
    download_images: bool = typer.Option(False, "--download-images", help="Download images locally"),
    pdf_support: bool = typer.Option(False, "--pdf-support", help="Convert PDFs"),
    content_selector: Optional[str] = typer.Option(None, "--content-selector", help="CSS for main content"),
    strip_selector: Optional[str] = typer.Option(None, "--strip-selector", help="CSS to strip"),
    download_assets: bool = typer.Option(False, "--download-assets", help="Download CSS/JS"),
    # Phase 3
    proxy: Optional[str] = typer.Option(None, "--proxy", help="Proxy URL"),
    headers: Optional[str] = typer.Option(None, "--headers", help="Custom headers JSON"),
    respect_robots: bool = typer.Option(False, "--respect-robots", help="Respect robots.txt"),
    timeout: int = typer.Option(30, "--timeout", help="Request timeout"),
    # Phase 4
    progress_file: str = typer.Option("_progress.json", "--progress-file", help="Progress file name"),
    html_report: bool = typer.Option(False, "--html-report", help="Generate HTML report"),
    diff_with: Optional[str] = typer.Option(None, "--diff-with", help="Path to manifest to diff"),
    notify_webhook: Optional[str] = typer.Option(None, "--notify-webhook", help="Webhook URL"),
    metrics_file: Optional[str] = typer.Option(None, "--metrics-file", help="Prometheus metrics file"),
    schema: bool = typer.Option(False)
):
    if schema:
        print(InputModel.model_json_schema_json(indent=2))
        return
        
    try:
        inputs = InputModel(
            url=url, 
            rate_limit=rate_limit, 
            batch_size=batch_size, 
            update=update, 
            max_pages=max_pages,
            concurrency=concurrency,
            include_pattern=include_pattern,
            exclude_pattern=exclude_pattern,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            priority_min=priority_min,
            changefreq=changefreq,
            extract_main=extract_main,
            download_images=download_images,
            pdf_support=pdf_support,
            content_selector=content_selector,
            strip_selector=strip_selector,
            download_assets=download_assets,
            proxy=proxy,
            headers=headers,
            respect_robots=respect_robots,
            timeout=timeout,
            progress_file=progress_file,
            html_report=html_report,
            diff_with=diff_with,
            notify_webhook=notify_webhook,
            metrics_file=metrics_file
        )
    except Exception as e:
        print(json.dumps(OutputModel(status="error", error=str(e)).model_dump()))
        sys.exit(1)
        
    try:
        asyncio.run(async_main(inputs))
    except KeyboardInterrupt:
        log("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(json.dumps(OutputModel(status="error", error=str(e)).model_dump()))
        sys.exit(1)

if __name__ == "__main__":
    app()
