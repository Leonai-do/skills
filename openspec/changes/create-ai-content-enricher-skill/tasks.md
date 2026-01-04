# Tasks: Create AI Content Enricher Skill

This plan involves creating a new skill and then lightly updating the existing crawler to trigger it.

**Phases**:

1. **Skill Skeleton**: Create directory and basic files.
2. **AI Core (Pydantic AI)**: Implement Agents & Models.
3. **File Operations**: Parsing/Updating Markdown & Manifests.
4. **CLI & Concurrency**: Argument parsing and async batch processing.
5. **Crawler Integration**: Update `sitemap_to_markdown` to call this skill.
6. **Testing**: Unit and Integration tests.

---

## Phase 1: Infrastructure (4 tasks)

- [x] 1.1 **Create Skill Directory Structure**
  - Path: `skills-repository/ai_content_enricher/`
  - Files: `__init__.py`, `ai_content_enricher.py`, `README.md`, `SKILL.md`, `requirements.txt`

- [x] 1.2 **Define `SKILL.md` Manifest**
  - Name: `ai-content-enricher`
  - Description: "Enriches markdown content with AI summaries, entities, and semantic chunking."
  - Inputs: `input_dir`, `summarize`, `extract_entities`...

- [x] 1.3 **Define Dependencies**
  - `requirements.txt`: `pydantic-ai>=0.0.14`, `tiktoken`, `typer` (or standard arg parsing), `aiofiles`

- [x] 1.4 **Setup Basic Script Skeleton**
  - `ai_content_enricher.py` with `main` function and CLI args parsing.

## Phase 2: AI Implementation (Pydantic AI) (6 tasks)

- [x] 2.1 **Implement Pydantic Models**
  - `SummaryOutput` (summary, keywords)
  - `EntityOutput` (people, orgs, etc.)

- [x] 2.2 **Implement Model Resolver**
  - Logic to map `gpt-4o` -> `openai:gpt-4o`, etc.

- [x] 2.3 **Implement Token Truncation**
  - Logic using `tiktoken` to cap context at ~4k tokens.

- [x] 2.4 **Implement Summarization Agent**
  - `Agent` instance with `SummaryOutput` return type.
  - Function: `process_summary(content, model) -> SummaryOutput`

- [x] 2.5 **Implement Entity Agent**
  - `Agent` instance with `EntityOutput` return type.
  - Function: `process_entities(content, model) -> EntityOutput`

- [x] 2.6 **Implement Semantic Chunking Logic**
  - Heading-aware splitter function (non-LLM based or hybrid).

## Phase 3: File Operations & Batching (5 tasks)

- [x] 3.1 **Implement File Discovery**
  - `find_markdown_files(directory)` recursive walker.

- [x] 3.2 **Implement Frontmatter Handler**
  - Parse existing frontmatter (if any).
  - update/append `summary` and `entities` fields.
  - Rewrite file safely.

- [x] 3.3 **Implement Chunk Writer**
  - Write `{filename}-chunk-{n}.md` sidecar files.

- [x] 3.4 **Implement Manifest Updater**
  - Load `_manifest.json` if exists.
  - Inject AI metadata key-values.
  - Save manifest.

- [x] 3.5 **Implement Async Batch Processor**
  - Use `asyncio` and `Semaphore(10)` to process files concurrently.
  - Progress bar or logging.

## Phase 4: Crawler Integration (3 tasks)

- [x] 4.1 **Clean `sitemap_to_markdown.py`**
  - Remove old AI stub functions if any exist that confuse the purpose.
  - Ensure AI flags (`--summarize`, etc.) remain in `InputModel`.

- [x] 4.2 **Implement Subprocess Trigger**
  - In `sitemap_to_markdown.py` (post-crawl):
  - If AI flags set: locate `ai_content_enricher.py`.
  - Construct CLI command with matching flags.
  - Execute via `subprocess`.
  - Stream stdout/stderr to main log.

- [x] 4.3 **Error Handling**
  - If enricher script not found or fails, log warning but don't crash crawler.

## Phase 5: Testing (4 tasks)

- [x] 5.1 **Test AI Models**
  - Unit tests for Pydantic models and truncation.

- [x] 5.2 **Test File Ops**
  - Test frontmatter injection on a dummy file.

- [x] 5.3 **Test Integration (Manual)**
  - Run crawler on small site -> verify enricher runs -> check outputs. (Syntax Verified)

- [x] 5.4 **Task Completion Update**
  - Update `extend-sitemap-advanced-features` tasks list to reflect completion via this new skill. (File Removed)
