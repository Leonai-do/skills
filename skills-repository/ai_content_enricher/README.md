# AI Content Enricher

A standalone skill to enrich Markdown content with AI-generated metadata.

## Usage

```bash
python ai_content_enricher.py --input-dir ./output --summarize --ai-api-key <YOUR_KEY>
```

## Features

- **Summarization**: Adds `summary` to YAML frontmatter.
- **Entity Extraction**: Adds `entities` to YAML frontmatter and `_manifest.json`.
- **Semantic Chunking**: Creates `*-chunk-*.md` files.
