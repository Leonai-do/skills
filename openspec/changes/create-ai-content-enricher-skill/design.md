# Design: AI Content Enricher Skill

## Context

We are separating the AI enrichment logic (Phase 6 of Sitemap) into a dedicated skill: `ai_content_enricher`. This skill will ingest Markdown files and use Pydantic AI to generate summaries, extract entities, and perform semantic chunking.

## Architecture

### 1. The `ai_content_enricher` Skill

**Entry Point**: `ai_content_enricher.py`
**CLI Interface**:

```bash
python ai_content_enricher.py \
  --input-dir ./output/docs \
  --summarize \
  --extract-entities \
  --semantic-chunk \
  --ai-api-key sk-... \
  --ai-model gpt-4o
```

**Core Components (Pydantic AI)**:

- `SummarizationAgent`: Compiles content -> `SummaryOutput`
- `EntityAgent`: Compiles content -> `EntityOutput`
- `ChunkingLogic`: Algorithmic splitting (heading-aware)

**Output Handling**:

- **In-place Update**: Appends/Updates YAML frontmatter in existing `.md` files (Summary, Entities).
- **Sidecar/Derivative**: Creates `*-chunk-*.md` files for chunks.
- **Manifest Update**: Updates `_manifest.json` if present in the input directory.

### 2. Integration with Sitemap Crawler

To maintain the "single command" UX, `sitemap_to_markdown.py` will use `subprocess` to call the new skill if AI flags are present.

**Flow**:

1. User runs: `sitemap_to_markdown --url ... --summarize`
2. Crawler finishes downloading to `./output`.
3. Crawler detects `--summarize` flag.
4. Crawler constructs command: `python ../ai_content_enricher/ai_content_enricher.py --input-dir ./output ...`
5. Crawler executes subprocess and streams output.

Alternatively, we can recommend a **Workflow** approach (chaining commands), but the user requested "deep integration" possible via command.

## Pydantic AI Implementation Details

(Preserved from previous design)

### Models

```python
class SummaryOutput(BaseModel):
    summary: str = Field(..., description="Concise 1-3 sentence summary")
    key_topics: list[str]

class EntityOutput(BaseModel):
    people: list[str]
    organizations: list[str]
    locations: list[str]
    dates: list[str]
    technologies: list[str]
```

### Token Management

- Use `tiktoken` to truncate content to ~4k tokens before sending to LLM.
- **Constraint**: The new skill handles all `tiktoken` dependencies.

## Data Flow Diagram

```
┌──────────────────────┐          ┌─────────────────────────┐
│ User / Workflow      │─────────▶│ sitemap_to_markdown.py  │
└──────────────────────┘          │ (Crawling Logic)        │
                                  └────────────┬────────────┘
                                               │
                                       (Files written to disk)
                                               ▼
                                  ┌─────────────────────────┐
                                  │ ./output/example.com/   │
                                  │  - index.md             │
                                  │  - about.md             │
                                  └────────────┬────────────┘
                                               │
        (Optional: Crawler calls subprocess)   │
        OR (User calls directly)               │
                                               ▼
┌──────────────────────┐          ┌─────────────────────────┐
│ Pydantic AI Provider │◀─────────│ ai_content_enricher.py  │
│ (OpenAI/Anthropic)   │          │ (Enrichment Logic)      │
└──────────────────────┘          └─────────────────────────┘
                                               │
                                     (Updates/New Files)
                                               ▼
                                  ┌─────────────────────────┐
                                  │ ./output/example.com/   │
                                  │  - index.md (Updated)   │
                                  │  - index-chunk-1.md     │
                                  └─────────────────────────┘
```

## Risks & Mitigations

1.  **Subprocess Reliability**: Ensure the crawler can find the new skill path.
    - _Mitigation_: Use relative path resolution or require skills to be in standard `skills-repository/` locations.
2.  **Concurrency**: Running AI on 1000 files takes time.
    - _Mitigation_: The new skill should implement `asyncio` with `Semaphore` to process files in parallel batches (e.g., 10 concurrent requests).

## Decision Record

- **Separation**: **YES**. New skill created.
- **Integration**: **Subprocess**. Crawler invokes enricher as a CLI tool. This avoids dependency pollution.
- **Framework**: **Pydantic AI**. Best for typed outputs.
