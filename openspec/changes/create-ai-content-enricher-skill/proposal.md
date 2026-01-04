# Change: Create AI Content Enricher Skill

## Why

The `sitemap_to_markdown` skill is becoming a monolithic "God Object". To follow the Single Responsibility Principle and enable AI processing on _any_ markdown content (not just crawled sites), we will implement the AI features (Phase 6 of the sitemap project) as a **standalone skill** called `ai_content_enricher`.

This separation allows:

1.  **Reusability**: Enrich any workspace docs, not just fresh crawls.
2.  **Stability**: Crawling (IO-bound) is decoupled from AI (Compute/Cost-bound).
3.  **Modularity**: Pydantic AI dependencies are isolated to the new skill.

## What Changes

### 1. New Skill: `ai_content_enricher`

- Create `skills-repository/ai_content_enricher/`
- Implement `ai_content_enricher.py` using **Pydantic AI**
- Features:
  - **Summarization**: Generates frontmatter summaries
  - **Entity Extraction**: Extracts People, Orgs, etc. to frontmatter/manifest
  - **Semantic Chunking**: Splits large files based on headings + headers
- Inputs: Directory path or single file path
- Dependencies: `pydantic-ai`, `tiktoken`, `logfire`

### 2. Integration with `sitemap_to_markdown`

- The crawler will **not** import `pydantic-ai`.
- Instead, it will have a "trigger" mechanism (e.g., calling the new skill via CLI or instructing the user to run it as a workflow step).
- _Strict Requirement_: The crawler must support a flag that automatically invokes this new skill on the output directory if requested, maintaining the user experience of a single command.

## Impact

- **New Capability**: `ai-completion` (or similar)
- **New Code**: `skills-repository/ai_content_enricher/*`
- **Affected Project**: `sitemap_to_markdown` (minor update to invoke new skill)
- **Dependencies**: `pydantic-ai` added _only_ to the new skill's environment.

## Test Strategy

1.  **Unit Tests**: Test logic in `ai_content_enricher` (models, agents, chunking).
2.  **Integration Tests**: Run the crawler, then run the enricher on the output, verifying the final markdown has summaries.
3.  **Standalone Tests**: Run the enricher on a static folder of markdown files.

## Reference Material

- Previous Pydantic AI design (migrated to this proposal).
- `skills-repository/sitemap_to_markdown/pydantic_ai_complete/` docs.
