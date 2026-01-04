import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import sitemap_to_markdown as stm

InputModel = stm.InputModel

def test_should_process_url_regex():
    inputs = InputModel(url="x", include_pattern=r"blog")
    assert stm.should_process_url("http://ex.com/blog/1", {}, inputs)
    assert not stm.should_process_url("http://ex.com/about", {}, inputs)

    inputs = InputModel(url="x", exclude_pattern=r"admin")
    assert stm.should_process_url("http://ex.com/blog", {}, inputs)
    assert not stm.should_process_url("http://ex.com/admin", {}, inputs)

def test_should_process_url_paths():
    # Comma separated
    inputs = InputModel(url="x", include_paths="/blog,/api")
    assert stm.should_process_url("http://ex.com/blog/1", {}, inputs)
    assert stm.should_process_url("http://ex.com/api/v1", {}, inputs)
    assert not stm.should_process_url("http://ex.com/about", {}, inputs)

    inputs = InputModel(url="x", exclude_paths="/admin")
    assert not stm.should_process_url("http://ex.com/admin/login", {}, inputs)

def test_should_process_url_priority():
    inputs = InputModel(url="x", priority_min=0.6)
    assert stm.should_process_url("x", {'priority': '0.8'}, inputs)
    assert stm.should_process_url("x", {'priority': '1.0'}, inputs)
    assert not stm.should_process_url("x", {'priority': '0.5'}, inputs)
    assert not stm.should_process_url("x", {'priority': '0.1'}, inputs)
    
    # Missing priority defaults to 0.5 < 0.6 -> False?
    # Logic: meta.get('priority', '0.5')
    assert not stm.should_process_url("x", {}, inputs) 

def test_should_process_url_changefreq():
    inputs = InputModel(url="x", changefreq="daily")
    assert stm.should_process_url("x", {'changefreq': 'daily'}, inputs)
    assert stm.should_process_url("x", {'changefreq': 'Daily'}, inputs) # Case insensitive check?
    # Code: inputs.changefreq.lower() vs meta...lower(). Yes.
    assert not stm.should_process_url("x", {'changefreq': 'monthly'}, inputs)
