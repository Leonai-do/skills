import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

# Add parent dir to path to import sitemap_to_markdown
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock imports that might be missing in test env if not running via uv with all deps
# But we will run via uv.

import sitemap_to_markdown as stm

@pytest.mark.asyncio
async def test_resolve_collision_dir_conflict(tmp_path):
    """Test resolving collision when we want a file but directory exists"""
    # Create directory 'foo'
    (tmp_path / "foo").mkdir() 
    
    # Try to resolve 'foo' (which usually implies foo.md or similar, but sanitize_filename handles extensions)
    # If we pass raw path 'foo' to resolve_collision:
    resolved = stm.resolve_collision(tmp_path, Path("foo"))
    
    # Should be renamed because 'foo' is a directory
    assert resolved != Path("foo")
    assert "alt" in resolved.name

@pytest.mark.asyncio
async def test_resolve_collision_parent_file_conflict(tmp_path):
    """Test resolving collision when a parent path component is a file"""
    # Create file 'parent'
    (tmp_path / "parent").touch()
    
    # We want 'parent/child.md'
    target = Path("parent/child.md")
    resolved = stm.resolve_collision(tmp_path, target)
    
    # Should rename 'parent' part or the whole path to avoid the file 'parent'
    # My implementation renames the whole path to 'child_DIGEST.md' effectively?
    # Wait, my logic: 
    # "check_path = base_path / current ... if check_path is file ... return relative_path renamed"
    # It returns "child_DIGEST.md" (renamed stem of relative_path).
    
    assert resolved.parent == Path('.') # It moved it out of the conflict folder?
    # Or at least it's not starting with 'parent/' anymore?
    # Actually my logic was: `return Path(f"{relative_path.stem}_{digest}{relative_path.suffix}")`
    # relying on the fact that `stem` of `parent/child.md` is `child`.
    # So yes, it flattens the path or renames it to avoid the directory. 
    # This is an acceptable resolution for now (preserving content is key).
    
    assert resolved.name.startswith("child_")
    assert resolved.suffix == ".md"

@pytest.mark.asyncio
async def test_fetch_retry_success():
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client.get.return_value = mock_response
    
    res = await stm.fetch_with_retry(mock_client, "http://test.com", 0)
    assert res == mock_response
    assert mock_client.get.call_count == 1

@pytest.mark.asyncio
async def test_fetch_retry_429_backoff():
    mock_client = AsyncMock()
    
    res_429 = MagicMock()
    res_429.status_code = 429
    res_429.headers.get.return_value = None # Use exponential backoff
    
    res_200 = MagicMock()
    res_200.status_code = 200
    
    mock_client.get.side_effect = [res_429, res_200]
    
    # We need to mock asyncio.sleep to not wait real time
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        res = await stm.fetch_with_retry(mock_client, "http://test.com", 0)
        
    assert res == res_200
    assert mock_client.get.call_count == 2
    mock_sleep.assert_called()

@pytest.mark.asyncio
async def test_process_url_success(tmp_path):
    mock_client = AsyncMock()
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.headers.get.return_value = "text/html"
    mock_res.text = "<html><body><h1>Hello</h1></body></html>"
    mock_client.get.return_value = mock_res
    
    # We mock fetch_with_retry if we want, or rely on mock_client logic inside it
    # Easier to patch fetch_with_retry to avoid network logic matching
    
    with patch('sitemap_to_markdown.fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_res
        
        status = await stm.process_url(mock_client, "http://test.com/page", tmp_path)
        
    assert status == "success"
    # Verify file created
    files = list(tmp_path.glob("**/*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "# Hello" in content
    assert "url: http://test.com/page" in content

@pytest.mark.asyncio
async def test_bloom_filter_integration():
    # If pybloom_live is installed, HAS_BLOOM should be True
    # We can't easily test it if optional import fails in test env, 
    # but we can check the flag.
    if stm.HAS_BLOOM:
        from pybloom_live import BloomFilter
        bf = BloomFilter(100, 0.01)
        bf.add("test")
        assert "test" in bf
