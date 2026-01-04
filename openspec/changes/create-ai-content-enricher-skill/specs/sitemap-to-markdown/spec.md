# sitemap-to-markdown Specification

## ADDED Requirements

### Requirement: AI Skill Orchestration

The system SHALL be capable of triggering the `ai_content_enricher` skill to process downloaded content.

#### Scenario: Workflow Integration

- **WHEN** the user runs `sitemap_to_markdown` with AI flags (e.g., `--summarize`, `--extract-entities`)
- **THEN** the system completes the crawl first
- **AND** automatically invokes the `ai_content_enricher` skill on the output directory using the provided flags and API keys
