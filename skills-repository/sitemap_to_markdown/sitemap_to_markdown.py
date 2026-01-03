#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "pydantic",
#     "requests",
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
from urllib.parse import urlparse
from typing import Optional, Iterator, Tuple, Dict, Any
from pathlib import Path

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

# --- 2. Define Output Schema ---
class OutputModel(BaseModel):
    status: str = Field(..., description="Status of execution: 'success' or 'error'")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data on success")
    error: Optional[str] = Field(None, description="Error message on failure")

# --- 3. Checkpoint Model ---
class Checkpoint(BaseModel):
    version: int = 1
    started_at: str
    last_updated: str
    source_url: str
    sitemap_type: str  # "single" or "index"
    sitemaps: list = []
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

def group_urls_hierarchically(urls: list) -> dict:
    """Group URLs by path segments"""
    groups = {}
    for url_data in urls:
        url = url_data['url']
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Extract first path segment or use root
        segments = path.split('/')
        group_key = f"/{segments[0]}" if segments and segments[0] else "/"
        
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(url_data)
    
    return groups

def generate_markdown(domain: str, sitemap_url: str, urls: list, total_urls: int) -> str:
    """Generate hierarchical Markdown from URL data"""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    md_lines = [
        f"# Sitemap: {domain}",
        "",
        f"**Generated**: {timestamp}",
        f"**Total URLs**: {total_urls:,}",
        f"**Source**: {sitemap_url}",
        "",
        "## URLs by Section",
        ""
    ]
    
    grouped = group_urls_hierarchically(urls)
    for group_key in sorted(grouped.keys()):
        md_lines.append(f"### {group_key}")
        md_lines.append("")
        
        for url_data in grouped[group_key]:
            url = url_data['url']
            meta = url_data['meta']
            
            meta_str = ""
            if 'lastmod' in meta:
                meta_str = f" - _lastmod: {meta['lastmod']}_"
            
            md_lines.append(f"- [{url}]({url}){meta_str}")
        
        md_lines.append("")
    
    return "\n".join(md_lines)

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
        inputs = InputModel(url=url, rate_limit=rate_limit, batch_size=batch_size)
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
        output_dir = os.path.join(script_dir, "output", domain)
        os.makedirs(output_dir, exist_ok=True)
        
        # 3. Check for checkpoint
        checkpoint_path = os.path.join(output_dir, "checkpoint.json")
        checkpoint = load_checkpoint(checkpoint_path)
        
        # 4. Fetch sitemap
        response = fetch_with_retry(sitemap_url, inputs.rate_limit)
        if not response:
            print(json.dumps(OutputModel(status="error", error=f"Failed to fetch sitemap: {sitemap_url}").model_dump()))
            sys.exit(1)
        
        xml_content = response.text
        
        # 5. Determine sitemap type
        is_sitemap_index = '<sitemapindex' in xml_content.lower()
        
        all_urls = []
        total_processed = checkpoint.total_processed if checkpoint else 0
        
        if is_sitemap_index:
            log("Processing sitemap index")
            child_sitemaps = extract_sitemap_index(xml_content)
            log(f"Found {len(child_sitemaps)} child sitemaps")
            
            for child_url in child_sitemaps:
                child_response = fetch_with_retry(child_url, inputs.rate_limit)
                if child_response:
                    for url, meta in stream_sitemap_urls(child_response.text):
                        all_urls.append({'url': url, 'meta': meta})
                        total_processed += 1
                        
                        # Checkpoint every N URLs
                        if total_processed % CHECKPOINT_INTERVAL == 0:
                            cp = Checkpoint(
                                started_at=datetime.utcnow().isoformat(),
                                last_updated=datetime.utcnow().isoformat(),
                                source_url=inputs.url,
                                sitemap_type="index",
                                total_processed=total_processed
                            )
                            save_checkpoint(checkpoint_path, cp)
        else:
            log("Processing single sitemap")
            for url, meta in stream_sitemap_urls(xml_content):
                all_urls.append({'url': url, 'meta': meta})
                total_processed += 1
                
                # Checkpoint every N URLs
                if total_processed % CHECKPOINT_INTERVAL == 0:
                    cp = Checkpoint(
                        started_at=datetime.utcnow().isoformat(),
                        last_updated=datetime.utcnow().isoformat(),
                        source_url=inputs.url,
                        sitemap_type="single",
                        total_processed=total_processed
                    )
                    save_checkpoint(checkpoint_path, cp)
        
        # 6. Generate markdown
        markdown_content = generate_markdown(domain, sitemap_url, all_urls, total_processed)
        
        # 7. Save markdown
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        filename = f"sitemap-{timestamp}.md"
        save_path = os.path.join(output_dir, filename)
        
        # Validate output path
        if not validate_output_path(save_path, script_dir):
            print(json.dumps(OutputModel(status="error", error="Invalid output path").model_dump()))
            sys.exit(1)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        log(f"Saved markdown to {save_path}")
        
        # 8. Clean up checkpoint
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
        
        # 9. Prepare response
        markdown_preview = markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content
        
        result = {
            "url": inputs.url,
            "sitemap_url": sitemap_url,
            "total_urls": total_processed,
            "saved_to": save_path,
            "markdown_preview": markdown_preview
        }
        
        print(json.dumps(OutputModel(status="success", data=result).model_dump()))
        
    except KeyboardInterrupt:
        log("Interrupted by user - checkpoint saved")
        sys.exit(130)
    except Exception as e:
        print(json.dumps(OutputModel(status="error", error=str(e)).model_dump()))
        sys.exit(1)

if __name__ == "__main__":
    app()
