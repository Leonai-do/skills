import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import sitemap_to_markdown as stm

# Correct InputModel usage requires mocking or proper instantiation
InputModel = stm.InputModel

@pytest.mark.asyncio
async def test_download_asset_image(tmp_path):
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake_image_data"
    mock_response.headers = {'content-type': 'image/jpeg'}
    mock_client.get.return_value = mock_response
    
    path = await stm.download_asset(mock_client, "http://ex.com/img.jpg", tmp_path, "images")
    
    assert path.startswith("_assets/images/img_")
    assert path.endswith(".jpg")
    assert (tmp_path / "_assets/images").exists()

@pytest.mark.asyncio
async def test_convert_pdf_to_markdown():
    # Mocking pypdf.PdfReader
    with patch('sitemap_to_markdown.PdfReader') as MockReader:
        instance = MockReader.return_value
        page = MagicMock()
        page.extract_text.return_value = "Page 1 Content"
        instance.pages = [page]
        
        text = stm.convert_pdf_to_markdown(b"pdf_bytes")
        assert "Page 1 Content" in text

@pytest.mark.asyncio
async def test_content_selector(tmp_path):
    mock_client = AsyncMock()
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.headers.get.return_value = "text/html"
    mock_res.text = "<html><body><div id='main'><h1>Title</h1><p>Content</p></div><div id='sidebar'>Ads</div></body></html>"
    mock_client.get.return_value = mock_res
    
    with patch('sitemap_to_markdown.fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_res
        
        inputs = InputModel(url="x", content_selector="#main")
        status = await stm.process_url(mock_client, "http://ex.com/page", tmp_path, inputs)
        
    assert status == "success"
    # Check if file contains Title but not Ads
    files = list(tmp_path.glob("**/*.md"))
    content = files[0].read_text()
    assert "Title" in content
    assert "Ads" not in content

@pytest.mark.asyncio
async def test_strip_selector(tmp_path):
    mock_client = AsyncMock()
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.headers.get.return_value = "text/html"
    mock_res.text = "<html><body><h1>Title</h1><div class='ad'>Buy Now</div></body></html>"
    mock_client.get.return_value = mock_res
    
    with patch('sitemap_to_markdown.fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_res
        
        inputs = InputModel(url="x", strip_selector=".ad")
        status = await stm.process_url(mock_client, "http://ex.com/page", tmp_path, inputs)
        
    files = list(tmp_path.glob("**/*.md"))
    content = files[0].read_text()
    assert "Title" in content
    assert "Buy Now" not in content
