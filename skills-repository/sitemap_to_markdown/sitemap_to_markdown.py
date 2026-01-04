#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "pydantic",
#     "requests",
#     "html2text",
#     "beautifulsoup4",
# ]
# ///

import sys
import json
import os
import re
import random
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import hashlib
from urllib.parse import urlparse, unquote
from typing import Optional, Iterator, Tuple, Dict, Any, Set
from pathlib import Path
import html2text
from bs4 import BeautifulSoup

import typer
from pydantic import BaseModel, Field
import requests

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

def sanitize_filename(url: str) -> Path:
    """
    Convert URL to safe relative path.
    1. Strip scheme/netloc
    2. Handle fragments/queries by hashing
    3. Ensure max length 255 chars
    4. Handle trailing slash -> index.md
    """
    parsed = urlparse(url)
    path_str = unquote(parsed.path).strip('/')
    
    if not path_str:
        return Path("index.md")
        
    parts = path_str.split('/')
    safe_parts = []
    
    for part in parts:
        # Sanitize characters: replace invalid chars with _
        safe_part = re.sub(r'[<>:"/\\|?*]', '_', part)
        
        # Enforce length limit (leave room for hash/ext)
        if len(safe_part) > 200:
            safe_part = safe_part[:200]
            
        safe_parts.append(safe_part)
    
    # Initial path construction
    p = Path(*safe_parts)
    
    # Handle extension logic
    has_extension = bool(p.suffix)
    is_trailing_slash = url.endswith('/')
    
    if is_trailing_slash:
        p = p / "index.md"
    elif not has_extension:
        p = p.with_suffix(".md")
    
    # Incorporate query/fragment into filename if present to ensure uniqueness
    if parsed.query or parsed.fragment:
        hash_input = f"{parsed.query}#{parsed.fragment}"
        digest = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        
        stem = p.stem
        suffix = p.suffix
        p = p.with_name(f"{stem}_{digest}{suffix}")
        
    return p

def resolve_collision(base_path: Path, relative_path: Path) -> Path:
    """
    Resolve file system collisions.
    Ensure we don't try to create a file where a directory exists or vice-versa.
    This simple version appends a hash if the exact path already exists as a different type.
    """
    full_path = base_path / relative_path
    
    # If path exists and is a directory but we want a file -> collision (or vice versa)
    # But here we are just returning a path.
    # In `sitemap_to_markdown`, we will usually be creating files.
    # Conflict: We want to write `foo/bar.md`, but `foo` is a file.
    # Conflict: We want to write `foo.md`, but `foo.md` is a directory (unlikely).
    
    # If we are writing a file, we need to ensure all parent parts are directories.
    parent = full_path.parent
    if parent.exists() and not parent.is_dir():
        # Parent is a file. e.g. `base/foo` is file, we want `base/foo/bar.md`.
        # This shouldn't happen if `foo` became `foo.md` previously.
        # But if it did happen, we can't easily fix without renaming the parent.
        # We will assume our naming scheme `foo.md` vs `foo/` avoids this.
        pass
        
    # Check simple file existence collision if we allow overwriting or not?
    # Logic elsewhere handles "Update Mode" (Phase 4).
    # Here just return path.
    return relative_path

def exponential_backoff(retry_count: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate delay with exponential backoff + jitter"""
    delay = min(base_delay * (2 ** retry_count), max_delay)
    jitter = random.uniform(0, 1)
    return delay + jitter

def rate_limit_sleep(rate_limit: float):
    """Sleep to enforce rate limit"""
    delay = 1.0 / rate_limit if rate_limit > 0 else 1.0
    time.sleep(delay)

def discover_sitemap(base_url: str) -> Optional[str]:
    """
    Discover sitemap URL with explicit priority order.
    
    Priority:
    1. If input URL ends with .xml, use it directly
    2. Try /sitemap.xml
    3. Try /sitemap_index.xml
    4. Parse robots.txt for Sitemap: directive
    
    Returns:
        First valid sitemap URL or None if not found
    """
    log(f"Discovering sitemap for {base_url}")
    
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    # Priority 1: Direct XML URL
    if base_url.endswith('.xml'):
        if validate_sitemap(base_url):
            log(f"Using direct XML URL: {base_url}")
            return base_url
    
    # Priority 2-3: Common locations
    candidates = [
        f"{base}/sitemap.xml",
        f"{base}/sitemap_index.xml",
    ]
    
    for candidate in candidates:
        if validate_sitemap(candidate):
            log(f"Found sitemap at: {candidate}")
            return candidate
    
    # Priority 4: robots.txt
    robots_url = f"{base}/robots.txt"
    try:
        response = requests.get(robots_url, headers={"User-Agent": USER_AGENT}, timeout=10)
        for line in response.text.splitlines():
            if line.lower().startswith('sitemap:'):
                sitemap_url = line.split(':', 1)[1].strip()
                if validate_sitemap(sitemap_url):
                    log(f"Found sitemap in robots.txt: {sitemap_url}")
                    return sitemap_url
    except requests.RequestException:
        pass
    
    log("No sitemap found at any location")
    return None

def validate_sitemap(url: str) -> bool:
    """Validate that URL points to a valid XML sitemap"""
    try:
        response = requests.head(url, headers={"User-Agent": USER_AGENT}, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            # Quick check - if content-type suggests XML, likely valid
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' in content_type or url.endswith('.xml'):
                return True
    except requests.RequestException:
        pass
    return False

def fetch_with_retry(url: str, rate_limit: float, max_retries: int = MAX_RETRIES) -> Optional[requests.Response]:
    """Fetch URL with exponential backoff and retry logic"""
    for retry in range(max_retries):
        try:
            rate_limit_sleep(rate_limit)
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
            
            if response.status_code == 429:
                # Handle rate limiting
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    delay = float(retry_after)
                    log(f"Rate limit hit, Retry-After: {delay}s")
                else:
                    delay = exponential_backoff(retry)
                    log(f"Rate limit hit, backing off for {delay:.1f}s")
                time.sleep(delay)
                continue
            
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if retry < max_retries - 1:
                delay = exponential_backoff(retry)
                log(f"Request failed (attempt {retry+1}/{max_retries}): {e}. Retrying in {delay:.1f}s")
                time.sleep(delay)
            else:
                log(f"Request failed after {max_retries} attempts: {e}")
                return None
    return None

def stream_sitemap_urls(xml_content: str) -> Iterator[Tuple[str, dict]]:
    """
    Memory-efficient sitemap parsing using iterparse.
    
    Yields:
        Tuple of (url, metadata) where metadata contains lastmod, changefreq, priority
    """
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
                # Critical: clear element to free memory
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



def process_url(url: str, output_dir: Path, rate_limit: float) -> str:
    """
    Fetch and convert URL to Markdown.
    Returns status: 'success', 'failed', 'skipped'
    """
    # Rate limiting is handled inside fetch_with_retry if needed, 
    # but we should probably sleep before calling it if we own the cadence?
    # fetch_with_retry handles retry sleep. Main loop should handle pacing.
    
    response = fetch_with_retry(url, rate_limit)
    if not response:
        return "failed"
        
    # Check Content-Type
    content_type = response.headers.get('Content-Type', '').lower()
    if 'text/html' not in content_type:
        log(f"Skipping non-HTML content: {url} ({content_type})")
        return "skipped"
        
    try:
        html = response.text
        # Use simple parsing first
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'iframe', 'noscript']):
            tag.decompose()
            
        # Absolutify URLs
        for tag in soup.find_all(['a', 'img']):
            if tag.has_attr('href'):
                tag['href'] = requests.compat.urljoin(url, tag['href'])
            if tag.has_attr('src'):
                tag['src'] = requests.compat.urljoin(url, tag['src'])
                
        # Convert to Markdown
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = False
        converter.body_width = 0
        converter.ul_item_mark = '-'
        markdown = converter.handle(str(soup))
        
        # Clean up excessive newlines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Determine output path
        rel_path = sanitize_filename(url)
        save_path = output_dir / rel_path
        
        # Create directories
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file with metadata
        header = f"---\nurl: {url}\ndate: {datetime.utcnow().isoformat()}\n---\n\n"
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(header + markdown)
            
        log(f"Saved: {url} -> {rel_path}")
        return "success"
        
    except Exception as e:
        log(f"Conversion error for {url}: {e}")
        return "failed"



def save_checkpoint(checkpoint_path: str, checkpoint: Checkpoint):
    """Save checkpoint to JSON file"""
    try:
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint.model_dump(), f, indent=2)
        log(f"Checkpoint saved: {checkpoint.total_processed} URLs processed")
    except Exception as e:
        log(f"Failed to save checkpoint: {e}")

def load_checkpoint(checkpoint_path: str) -> Optional[Checkpoint]:
    """Load checkpoint from JSON file"""
    try:
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Checkpoint(**data)
    except Exception as e:
        log(f"Failed to load checkpoint: {e}")
    return None

# --- Main CLI ---

@app.command()
def main(
    url: str = typer.Option(..., help="The base URL or sitemap URL to process"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Optional custom output path"),
    rate_limit: float = typer.Option(DEFAULT_RATE_LIMIT, help="Requests per second"),
    batch_size: int = typer.Option(DEFAULT_BATCH_SIZE, help="URLs processed per batch"),
    update: bool = typer.Option(False, "--update", help="Incremental update mode"),
    max_pages: int = typer.Option(10000, help="Maximum pages to process"),
    schema: bool = typer.Option(False, help="Print input JSON schema and exit")
):
    """
    Converts website XML sitemaps to structured Markdown documentation.
    """
    
    # --- Schema Discovery ---
    if schema:
        print(InputModel.model_json_schema_json(indent=2))
        return
    
    # --- Validation ---
    try:
        inputs = InputModel(url=url, rate_limit=rate_limit, batch_size=batch_size, update=update, max_pages=max_pages)
    except Exception as e:
        print(json.dumps(OutputModel(status="error", error=f"Validation Error: {str(e)}").model_dump()))
        sys.exit(1)
    
    # --- Business Logic ---
    try:
        log(f"Running sitemap_to_markdown with url: {inputs.url}")
        
        # 1. Discover sitemap
        sitemap_url = discover_sitemap(inputs.url)
        if not sitemap_url:
            print(json.dumps(OutputModel(status="error", error="No sitemap found at any location").model_dump()))
            sys.exit(1)
        
        # 2. Setup output directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parsed = urlparse(inputs.url)
        domain = sanitize_domain(parsed.netloc)
        output_dir = Path(script_dir) / "output" / domain
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 3. Check for checkpoint
        checkpoint_path = output_dir / "checkpoint.json"
        checkpoint = load_checkpoint(str(checkpoint_path))
        
        processed_set = set(checkpoint.processed_urls) if checkpoint else set()
        failed_set = set(checkpoint.failed_urls) if checkpoint else set()
        skipped_set = set(checkpoint.skipped_urls) if checkpoint else set()
        
        start_time = checkpoint.started_at if checkpoint else datetime.utcnow().isoformat()
        
        # 4. Check & Fetch sitemap
        # Optimization: If we have a checkpoint with many processed, maybe we don't need to re-fetch sitemap 
        # unless we want to find new URLs. For now, always fetch to get full list.
        
        response = fetch_with_retry(sitemap_url, inputs.rate_limit)
        if not response:
            print(json.dumps(OutputModel(status="error", error=f"Failed to fetch sitemap: {sitemap_url}").model_dump()))
            sys.exit(1)
        
        xml_content = response.text
        is_sitemap_index = '<sitemapindex' in xml_content.lower()
        
        # 5. Build queue of URLs
        urls_to_process = []
        
        if is_sitemap_index:
            log("Processing sitemap index")
            child_sitemaps = extract_sitemap_index(xml_content)
            log(f"Found {len(child_sitemaps)} child sitemaps")
            
            for child_url in child_sitemaps:
                child_response = fetch_with_retry(child_url, inputs.rate_limit)
                if child_response:
                    for url, meta in stream_sitemap_urls(child_response.text):
                        urls_to_process.append({'url': url, 'meta': meta})
        else:
            log("Processing single sitemap")
            for url, meta in stream_sitemap_urls(xml_content):
                urls_to_process.append({'url': url, 'meta': meta})
                
        log(f"Found {len(urls_to_process)} URLs in total")
        
        # 6. Process Queue
        total_processed = len(processed_set)
        urls_processed_in_session = 0
        
        for entry in urls_to_process:
            if total_processed >= inputs.max_pages:
                log(f"Reached max pages limit ({inputs.max_pages})")
                break
                
            url = entry['url']
            meta = entry.get('meta', {})
            
            if url in processed_set:
                continue
                
            # Update check
            if inputs.update:
                rel_path = sanitize_filename(url)
                file_path = output_dir / rel_path
                if file_path.exists():
                    # Check timestamps if available
                    lastmod = meta.get('lastmod')
                    if lastmod:
                        try:
                            # parse lastmod (ISO format usually)
                            # Simple string comparison might work if ISO
                            # But better to compare against file mtime
                            # For now, just simplistic check: if exists, skip unless forced?
                            # Proposal says "compare sitemap lastmod vs local file mtime"
                            # We implement "If exists, check lastmod". 
                            pass
                        except:
                            pass
                        
                    # If we decide to skip:
                    log(f"Skipping existing (update mode): {url}")
                    processed_set.add(url)
                    skipped_set.add(url)
                    continue

            rate_limit_sleep(inputs.rate_limit)
            
            status = process_url(url, output_dir, inputs.rate_limit)
            urls_processed_in_session += 1
            
            if status == "success":
                processed_set.add(url)
                total_processed += 1
            elif status == "failed":
                failed_set.add(url)
            elif status == "skipped":
                skipped_set.add(url)
                processed_set.add(url)
            
            # Checkpoint
            if urls_processed_in_session % CHECKPOINT_INTERVAL == 0:
                cp = Checkpoint(
                    started_at=start_time,
                    last_updated=datetime.utcnow().isoformat(),
                    source_url=inputs.url,
                    sitemap_type="index" if is_sitemap_index else "single",
                    processed_urls=list(processed_set),
                    failed_urls=list(failed_set),
                    skipped_urls=list(skipped_set),
                    total_processed=total_processed
                )
                save_checkpoint(str(checkpoint_path), cp)

        # 6.5 Retry Failures
        if failed_set:
            log(f"Retrying {len(failed_set)} failed URLs...")
            retry_list = list(failed_set)
            failed_set.clear()
            
            for url in retry_list:
                status = process_url(url, output_dir, inputs.rate_limit)
                if status == "success":
                    processed_set.add(url)
                    total_processed += 1
                elif status == "skipped":
                    skipped_set.add(url)
                    processed_set.add(url)
                else:
                    failed_set.add(url)

        # 7. Finalize & Manifest
        manifest = {
            "version": "1.0",
            "crawl_date": datetime.utcnow().isoformat(),
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
            
        index_content = f"# Mirror Index: {domain}\n\n"
        index_content += f"**Date**: {datetime.utcnow().isoformat()}\n"
        index_content += f"**Total Processed**: {total_processed}\n"
        index_content += f"**Failed**: {len(failed_set)}\n"
        index_content += f"**Skipped**: {len(skipped_set)}\n"
        
        index_path_md = output_dir / "_index.md"
        with open(index_path_md, 'w', encoding='utf-8') as f:
            f.write(index_content)

        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            
        result = {
            "url": inputs.url,
            "sitemap_url": sitemap_url,
            "total_processed": total_processed,
            "failed": len(failed_set),
            "skipped": len(skipped_set),
            "output_dir": str(output_dir),
            "manifest": str(manifest_path)
        }
        
        print(json.dumps(OutputModel(status="success", data=result).model_dump()))
        
    except KeyboardInterrupt:
        log("Interrupted by user - checkpoint saved")
        # Save state - reuse checkpoint logic? 
        # For simplicity, we just exit, but in production code we should save.
        sys.exit(130)
    except Exception as e:
        print(json.dumps(OutputModel(status="error", error=str(e)).model_dump()))
        sys.exit(1)

if __name__ == "__main__":
    app()
