import pytest
import sys
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
import sitemap_to_markdown as stm

# Test the format converter functions
def test_convert_to_json():
    """Test JSON format converter"""
    from bs4 import BeautifulSoup
    
    url = "http://example.com/page"
    html = "<html><head><title>Test Page</title></head><body><p>Content</p></body></html>"
    soup = BeautifulSoup(html, 'html.parser')
    
    result = stm.convert_to_json(url, html, soup, {"key": "value"})
    
    assert result['url'] == url
    assert result['html'] == html
    assert result['title'] == "Test Page"
    assert 'test page' in result['text'].lower() or 'content' in result['text'].lower()
    assert result['metadata']['key'] == "value"
    assert 'fetched_at' in result

def test_convert_to_html_wrapped():
    """Test HTML wrapper format converter"""
    from bs4 import BeautifulSoup
    
    url = "http://example.com/page"
    html = "<html><body><h1>Title</h1><h2>Subtitle</h2><p>Content</p></body></html>"
    soup = BeautifulSoup(html, 'html.parser')
    
    result = stm.convert_to_html_wrapped(url, soup)
    
    assert '<!DOCTYPE html>' in result
    assert url in result
    assert 'Table of Contents' in result
    assert 'Title' in result
    assert 'Subtitle' in result

def test_convert_to_text():
    """Test plain text converter"""
    from bs4 import BeautifulSoup
    
    html = "<html><body><h1>Title</h1><script>alert('test')</script><p>Paragraph</p></body></html>"
    soup = BeautifulSoup(html, 'html.parser')
    
    result = stm.convert_to_text(soup)
    
    assert 'Title' in result
    assert 'Paragraph' in result
    # Script content should be included (BeautifulSoup extracts all text)
    assert len(result) \u003e 0

@pytest.mark.asyncio
async def test_process_url_json_format(tmp_path):
    """Test process_url with JSON output format"""
    mock_client = AsyncMock()
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.headers.get.return_value = "text/html"
    mock_res.text = "<html><body><h1>Test</h1></body></html>"
    
    from unittest.mock import patch
    with patch('sitemap_to_markdown.fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_res
        
        inputs = stm.InputModel(url="x", output_format="json")
        status = await stm.process_url(mock_client, "http://test.com/page", tmp_path, inputs)
        
    assert status == "success"
    # Check JSON file was created
    json_files = list(tmp_path.glob("**/*.json"))
    assert len(json_files) == 1
    
    with open(json_files[0]) as f:
        data = json.load(f)
    assert data['url'] == "http://test.com/page"
    assert 'html' in data

@pytest.mark.asyncio
async def test_process_url_html_format(tmp_path):
    """Test process_url with HTML output format"""
    mock_client = AsyncMock()
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.headers.get.return_value = "text/html"
    mock_res.text = "<html><body><h1>Test</h1></body></html>"
    
    from unittest.mock import patch
    with patch('sitemap_to_markdown.fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_res
        
        inputs = stm.InputModel(url="x", output_format="html")
        status = await stm.process_url(mock_client, "http://test.com/page", tmp_path, inputs)
        
    assert status == "success"
    html_files = list(tmp_path.glob("**/*.html"))
    assert len(html_files) == 1
    
    content = html_files[0].read_text()
    assert '<!DOCTYPE html>' in content

@pytest.mark.asyncio  
async def test_process_url_text_format(tmp_path):
    """Test process_url with text output format"""
    mock_client = AsyncMock()
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.headers.get.return_value = "text/html"
    mock_res.text = "<html><body><h1>Heading</h1><p>Paragraph</p></body></html>"
    
    from unittest.mock import patch
    with patch('sitemap_to_markdown.fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_res
        
        inputs = stm.InputModel(url="x", output_format="text")
        status = await stm.process_url(mock_client, "http://test.com/page", tmp_path, inputs)
        
    assert status == "success"
    txt_files = list(tmp_path.glob("**/*.txt"))
    assert len(txt_files) == 1
    
    content = txt_files[0].read_text()
    assert 'Heading' in content
    assert 'Paragraph' in content
