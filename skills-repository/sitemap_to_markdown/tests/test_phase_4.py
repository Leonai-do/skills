import pytest
import sys
import json
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import sitemap_to_markdown as stm

InputModel = stm.InputModel
ProgressStats = stm.ProgressStats

def test_progress_stats_serialization():
    stats = ProgressStats(
        processed=10,
        total=100,
        failed=1,
        skipped=2,
        elapsed_sec=5.5,
        eta_sec=45.0,
        current_url="http://x.com/page"
    )
    dumped = stats.model_dump()
    assert dumped['processed'] == 10
    assert dumped['eta_sec'] == 45.0

def test_write_prometheus_metrics(tmp_path):
    stats = ProgressStats(
        processed=10,
        total=100,
        failed=1,
        skipped=2,
        elapsed_sec=5.5,
        eta_sec=45.0
    )
    metric_file = tmp_path / "metrics.prom"
    stm.write_prometheus_metrics(metric_file, stats)
    
    content = metric_file.read_text()
    assert "sitemap_urls_total 100" in content
    assert "sitemap_urls_processed 10" in content
    assert "# TYPE sitemap_urls_total gauge" in content

@pytest.mark.asyncio
async def test_webhook_payload():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        payload = {"status": "test"}
        await stm.send_webhook("http://hook.com", payload)
        mock_post.assert_awaited_with("http://hook.com", json=payload, timeout=10)

def test_html_report_generation(tmp_path):
    # Mock jinja2 Template if strictly necessary, but if listed in test request we can assume it's there
    # or handle ImportError gracefully as done in code.
    # We'll just define manifest manually.
    manifest = {
        "source_url": "http://x.com",
        "statistics": {"total_processed": 50, "failed": 2, "skipped": 0},
        "crawl_date": "2023-01-01",
        "failed_urls": ["http://x.com/f1", "http://x.com/f2"]
    }
    
    # We need to rely on the module having imported Template.
    # If not present in environment, function returns early.
    
    with patch("sitemap_to_markdown.Template") as MockTemplate:
        mock_t_instance = MockTemplate.return_value
        mock_t_instance.render.return_value = "<html>Report</html>"
        
        stm.generate_html_report(tmp_path, manifest)
        
        report_file = tmp_path / "_report.html"
        assert report_file.read_text() == "<html>Report</html>"
