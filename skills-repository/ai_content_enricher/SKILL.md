---
name: ai-content-enricher
description: Enriches markdown content with AI summaries, entities, and semantic chunking using Pydantic AI.
version: 1.0.0
usage: |
  python ai_content_enricher.py --input-dir <dir> [options]

  Options:
    --input-dir STR           Directory containing markdown files (required)
    --summarize               Enable summarization
    --extract-entities        Enable entity extraction
    --semantic-chunk          Enable semantic chunking
    --ai-model STR            Model name (default: gpt-4o)
    --concurrency INT         Number of concurrent files to process (default: 5)
    
    # Provider Authentication & Configuration
    --ai-api-key STR          Generic API Key (fallback/override)
    
    --openai-api-key STR      OpenAI API Key
    --openai-base-url STR     OpenAI Base URL
    --anthropic-api-key STR   Anthropic API Key
    --anthropic-base-url STR  Anthropic Base URL
    --google-api-key STR      Google/Gemini API Key
    --deepseek-api-key STR    DeepSeek API Key
    --deepseek-base-url STR   DeepSeek Base URL
    --ollama-api-key STR      Ollama Cloud API Key
    --ollama-base-url STR     Ollama Base URL (e.g. https://api.ollama.com)
    --zai-api-key STR         Z.ai API Key
    --hf-api-key STR          HuggingFace API Key
---

# AI Content Enricher

This skill processes a directory of Markdown files and enriches them using LLMs via Pydantic AI.

## Capabilities

1.  **Summarization**: Generates a concise summary and key topics, adding them to the file's frontmatter.
2.  **Entity Extraction**: Extracts people, organizations, locations, dates, and technologies, adding them to the frontmatter and updateing `_manifest.json` if available.
3.  **Semantic Chunking**: Splits large documents into semantically meaningful chunks based on headers and token limits, saving them as sidecar files.

## Dependencies

- **pydantic-ai**: For type-safe LLM interactions.
- **tiktoken**: For token counting and truncation.
- **aiofiles**: For async file I/O.
- **typer**: For CLI interface.
