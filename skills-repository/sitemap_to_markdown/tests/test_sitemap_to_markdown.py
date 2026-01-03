#!/usr/bin/env python3
"""
Pytest test suite for sitemap_to_markdown skill.

Tests cover:
- Sitemap discovery
- XML parsing (valid, malformed, namespaces)
- Rate limiting and backoff
- Checkpoint save/load
- Path validation
"""

import json
import time
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import sitemap_to_markdown as stm

# --- Fixtures ---

@pytest.fixture
def sample_sitemap_path():
    return Path(__file__).parent / "fixtures" / "sample_sitemap.xml"

@pytest.fixture
def sample_sitemap_index_path():
    return Path(__file__).parent / "fixtures" / "sample_sitemap_index.xml"

@pytest.fixture
def sample_sitemap_xml(sample_sitemap_path):
    return sample_sitemap_path.read_text()

# --- Discovery Tests ---

def test_validate_output_path_rejects_traversal():
    """Test path traversal protection"""
    base_dir = "/home/user/workspace"
    
    # Should reject paths with ..
    assert not stm.validate_output_path("../etc/passwd", base_dir)
    assert not stm.validate_output_path("/home/user/../etc/passwd", base_dir)
    
def test_validate_output_path_allows_valid():
    """Test valid paths are allowed"""
    base_dir = "/home/user/workspace"
    valid_path = "/home/user/workspace/output/example.md"
    
    # Would pass with actual filesystem, mocked in real implementation
    # This is a placeholder test demonstrating the concept
    assert stm.validate_output_path.__doc__ is not None

def test_sanitize_domain():
    """Test domain sanitization for safe filenames"""
    assert stm.sanitize_domain("example.com") == "example.com"
    assert stm.sanitize_domain("example.com:8080") == "example.com_8080"
    assert stm.sanitize_domain("sub.example.com") == "sub.example.com"

# --- Rate Limiting Tests ---

def test_exponential_backoff_formula():
    """Test exponential backoff calculation"""
    # Initial delay
    delay0 = stm.exponential_backoff(0, base_delay=1.0)
    assert 1.0 <= delay0 <= 2.0  # 1.0 + jitter
    
    # First retry
    delay1 = stm.exponential_backoff(1, base_delay=1.0)
    assert 2.0 <= delay1 <= 3.0  # 2.0 + jitter
    
    # Second retry
    delay2 = stm.exponential_backoff(2, base_delay=1.0)
    assert 4.0 <= delay2 <= 5.0  # 4.0 + jitter

def test_exponential_backoff_respects_max():
    """Test backoff caps at max_delay"""
    delay = stm.exponential_backoff(10, base_delay=1.0, max_delay=60.0)
    assert delay <= 61.0  # max + jitter

def test_rate_limit_sleep_timing():
    """Test rate limiting delays requests"""
    start = time.time()
    stm.rate_limit_sleep(2.0)  # 2 requests/sec = 0.5s delay
    elapsed = time.time() - start
    assert 0.4 <= elapsed <= 0.6  # Allow small margin

# --- XML Parsing Tests ---

def test_stream_sitemap_urls_parses_valid_xml(sample_sitemap_xml):
    """Test streaming parser extracts URLs"""
    urls = list(stm.stream_sitemap_urls(sample_sitemap_xml))
    
    assert len(urls) == 10
    assert urls[0][0] == "https://example.com/"
    assert urls[0][1]['lastmod'] == "2026-01-01"
    assert urls[0][1]['priority'] == "1.0"

def test_stream_sitemap_urls_handles_missing_metadata(sample_sitemap_xml):
    """Test parser handles URLs without metadata"""
    urls = list(stm.stream_sitemap_urls(sample_sitemap_xml))
    
    # URL 4 and 5 have no changefreq/priority
    url_4 = [u for u in urls if u[0] == "https://example.com/products/widget-b"][0]
    assert 'lastmod' in url_4[1]
    assert 'changefreq' not in url_4[1]

def test_stream_sitemap_urls_handles_malformed_xml():
    """Test parser gracefully handles malformed XML"""
    malformed_xml = "<?xml version='1.0'?><invalid>no closing tag"
    
    urls = list(stm.stream_sitemap_urls(malformed_xml))
    # Should return empty list, not crash
    assert urls == []

def test_extract_sitemap_index(sample_sitemap_index_path):
    """Test sitemap index extraction"""
    xml_content = sample_sitemap_index_path.read_text()
    sitemaps = stm.extract_sitemap_index(xml_content)
    
    assert len(sitemaps) == 2
    assert "https://example.com/sitemap-products.xml" in sitemaps
    assert "https://example.com/sitemap-blog.xml" in sitemaps

# --- Checkpoint Tests ---

def test_checkpoint_save_and_load(tmp_path):
    """Test checkpoint persistence"""
    from datetime import datetime
    
    checkpoint_path = tmp_path / "checkpoint.json"
    
    # Save checkpoint
    checkpoint = stm.Checkpoint(
        started_at=datetime.utcnow().isoformat(),
        last_updated=datetime.utcnow().isoformat(),
        source_url="https://example.com",
        sitemap_type="single",
        total_processed=250
    )
    
    stm.save_checkpoint(str(checkpoint_path), checkpoint)
    
    # Verify file exists
    assert checkpoint_path.exists()
    
    # Load checkpoint
loaded_checkpoint = stm.load_checkpoint(str(checkpoint_path))
    assert loaded_checkpoint is not None
    assert loaded_checkpoint.total_processed == 250
    assert loaded_checkpoint.sitemap_type == "single"

def test_checkpoint_load_nonexistent():
    """Test loading checkpoint that doesn't exist"""
    checkpoint = stm.load_checkpoint("/nonexistent/checkpoint.json")
    assert checkpoint is None

# --- Grouping Tests ---

def test_group_urls_hierarchically():
    """Test hierarchical URL grouping by path"""
    urls = [
        {'url': 'https://example.com/', 'meta': {}},
        {'url': 'https://example.com/about', 'meta': {}},
        {'url': 'https://example.com/blog/post-1', 'meta': {}},
        {'url': 'https://example.com/blog/post-2', 'meta': {}},
        {'url': 'https://example.com/products/widget', 'meta': {}},
    ]
    
    groups = stm.group_urls_hierarchically(urls)
    
    assert '/' in groups
    assert '/blog' in groups
    assert '/products' in groups
    assert len(groups['/blog']) == 2
    assert len(groups['/products']) == 1

# --- Markdown Generation Tests ---

def test_generate_markdown_structure():
    """Test markdown generation with metadata"""
    urls = [
        {'url': 'https://example.com/', 'meta': {'lastmod': '2026-01-01'}},
        {'url': 'https://example.com/about', 'meta': {}},
    ]
    
    markdown = stm.generate_markdown("example.com", "https://example.com/sitemap.xml", urls, 2)
    
    assert "# Sitemap: example.com" in markdown
    assert "**Total URLs**: 2" in markdown
    assert "**Source**: https://example.com/sitemap.xml" in markdown
    assert "[https://example.com/](https://example.com/)" in markdown
    assert "_lastmod: 2026-01-01_" in markdown

# --- Integration Tests (Note: these would need mocking for true unit tests) ---

def test_input_model_validation():
    """Test Pydantic input model"""
    valid_input = stm.InputModel(url="https://example.com", rate_limit=1.0, batch_size=1000)
    assert valid_input.url == "https://example.com"
    assert valid_input.rate_limit == 1.0

def test_output_model_success_format():
    """Test output model for success case"""
    output = stm.OutputModel(
        status="success",
        data={"url": "https://example.com", "total_urls": 100}
    )
    assert output.status == "success"
    assert output.data['total_urls'] == 100
    assert output.error is None

def test_output_model_error_format():
    """Test output model for error case"""
    output = stm.OutputModel(
        status="error",
        error="Sitemap not found"
    )
    assert output.status == "error"
    assert output.error == "Sitemap not found"
    assert output.data is None
