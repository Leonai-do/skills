import sys
from pathlib import Path
from unittest.mock import MagicMock

# Create mocks for external modules
sys.modules["html2text"] = MagicMock()
sys.modules["bs4"] = MagicMock()
sys.modules["requests"] = MagicMock()

# Typer mock
typer_mock = MagicMock()
sys.modules["typer"] = typer_mock

# Pydantic mock - needs to support inheritance for BaseModel
pydantic_mock = MagicMock()
class MockBaseModel:
    pass
pydantic_mock.BaseModel = MockBaseModel
pydantic_mock.Field = MagicMock()
sys.modules["pydantic"] = pydantic_mock

# Add parent directory to path to import sitemap_to_markdown
sys.path.insert(0, str(Path(__file__).parent.parent))
import sitemap_to_markdown as stm

def test_sanitize_filename_simple():
    url = "https://example.com/foo/bar"
    # Expect implicit .md since no extension
    assert stm.sanitize_filename(url) == Path("foo/bar.md")

def test_sanitize_filename_root():
    url = "https://example.com"
    assert stm.sanitize_filename(url) == Path("index.md")
    url = "https://example.com/"
    assert stm.sanitize_filename(url) == Path("index.md")

def test_sanitize_filename_extension():
    # Current logic preserves extension if present
    url = "https://example.com/foo.html"
    assert stm.sanitize_filename(url) == Path("foo.html")

def test_sanitize_filename_queries():
    url = "https://example.com/foo?q=bar"
    path = stm.sanitize_filename(url)
    assert "_" in path.stem
    assert path.suffix == ".md"

def test_sanitize_filename_fragments():
    url = "https://example.com/foo#section"
    path = stm.sanitize_filename(url)
    assert "_" in path.stem
    assert path.suffix == ".md"

def test_sanitize_filename_long():
    long_segment = "a" * 300
    url = f"https://example.com/{long_segment}"
    path = stm.sanitize_filename(url)
    # 200 prefix + hash (8) + separator (1) + suffix (.md 3) approx
    assert len(path.name) <= 255

if __name__ == "__main__":
    try:
        test_sanitize_filename_simple()
        test_sanitize_filename_root()
        test_sanitize_filename_extension()
        test_sanitize_filename_queries()
        test_sanitize_filename_fragments()
        test_sanitize_filename_long()
        print("All tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
