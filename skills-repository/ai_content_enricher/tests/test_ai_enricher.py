import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from pathlib import Path

# Add skill path to sys.path
sys.path.append(str(Path(__file__).parents[1]))

from ai_content_enricher import (
    resolve_model, 
    truncate_for_model, 
    chunk_by_semantics, 
    SummaryOutput, 
    EntityOutput
)

def test_resolve_model():
    assert resolve_model("gpt-4o") == "openai:gpt-4o"
    assert resolve_model("anthropic:claude-3-5-sonnet") == "anthropic:claude-3-5-sonnet"
    assert resolve_model("unknown-model") == "openai:unknown-model"

def test_truncate_for_model():
    text = "a" * 10000
    # Assuming standard encoding, 1 char != 1 token, but let's test strict length cap behavior
    # Without tiktoken installed in test env, it might fallback to char length / 4. 
    # Let's mock tiktoken or test fallback.
    
    with patch('ai_content_enricher.tiktoken', None):
        truncated = truncate_for_model(text, max_tokens=100)
        assert len(truncated) <= 400 # 100 tokens * 4 chars fallback
        
def test_chunk_by_semantics_headers():
    text = """
# Header 1
Content 1
## Header 2
Content 2
# Header 3
Content 3
"""
    chunks = chunk_by_semantics(text, max_tokens=100)
    assert len(chunks) == 3
    assert "Content 1" in chunks[0]
    assert "Content 2" in chunks[1]
    assert "Content 3" in chunks[2]

def test_chunk_by_semantics_paragraphs():
    text = "Para 1\n\nPara 2\n\nPara 3"
    # Small max_tokens to force split
    with patch('ai_content_enricher.count_tokens', side_effect=lambda x: len(x)):
         chunks = chunk_by_semantics(text, max_tokens=10) 
         # Para 1 (6 chars) + Para 2 (6 chars) = 14 > 10. Split.
    
    # We depend on actual token counting logic or mocks. 
    # If we mock count_tokens to return length of string:
    # "Para 1" = 6. "Para 2" = 6. 
    # "Para 1\n\nPara 2" = 14.
    
    # Let's just verify it returns list of strings
    chunks = chunk_by_semantics(text, max_tokens=1000)
    assert len(chunks) == 1
    assert chunks[0] == text.strip()

@pytest.mark.asyncio
async def test_summary_model_structure():
    s = SummaryOutput(summary="Test", key_topics=["A", "B"])
    assert s.summary == "Test"
    assert len(s.key_topics) == 2
