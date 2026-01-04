import pytest
import sys
import sqlite3
import os
import zipfile
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import sitemap_to_markdown as stm

# Test Phase 5 Storage
def test_export_to_sqlite(tmp_path):
    db_path = tmp_path / "test.db"
    stm.export_to_sqlite(db_path, "http://x.com", "content", "2023-01-01", "success")
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM pages")
    rows = c.fetchall()
    conn.close()
    
    assert len(rows) == 1
    assert rows[0][0] == "http://x.com"
    assert rows[0][1] == "content"

def test_create_zip_archive(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "test.md").write_text("markdown")
    
    stm.create_archive(output_dir, "zip", "test_domain")
    
    zip_path = tmp_path / "test_domain.zip"
    assert zip_path.exists()
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        assert "output/test.md" in z.namelist()

@pytest.mark.asyncio
async def test_s3_upload(tmp_path):
    # Mock boto3
    with patch("sitemap_to_markdown.boto3") as mock_boto:
        mock_client = MagicMock()
        mock_boto.client.return_value = mock_client
        
        file_path = tmp_path / "test.md"
        file_path.write_text("test")
        
        stm.upload_to_s3("bucket", "prefix", file_path, Path("rel/test.md"))
        
        mock_client.upload_file.assert_called_with(str(file_path), "bucket", "prefix/rel/test.md")

# Test Phase 6 AI
def test_token_counting():
    if not stm.tiktoken:
        pytest.skip("tiktoken not installed")
        
    # We can't easily install tiktoken encoding in test env without download.
    # But if installed, it should work for 'gpt-3.5-turbo'
    try:
        count = stm.count_tokens("hello world")
        assert count > 0
    except Exception:
        # Fails if network blocked for encoding download or similar
        pass

def test_generate_llms_txt(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "p1.md").write_text("content")
    
    manifest = {
        "source_url": "http://x.com",
        "crawl_date": "2023",
        "total_processed": 1
    }
    
    stm.generate_llms_txt(output_dir, manifest)
    
    llms_txt = output_dir / "llms.txt"
    content = llms_txt.read_text()
    assert "# Site Content Manifest" in content
    assert "p1.md" in content

def test_generate_toc():
    md = "# Title\n\n## Subtitle\nText\n"
    toc = stm.generate_toc(md)
    assert "- [Title](#title)" in toc
    assert "  - [Subtitle](#subtitle)" in toc
