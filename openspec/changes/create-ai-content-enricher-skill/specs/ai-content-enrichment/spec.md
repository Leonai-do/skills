# ai-content-enrichment Specification

## ADDED Requirements

### Requirement: AI Content Enrichment

The system SHALL provide a mechanism to enrich Markdown content with AI-generated metadata using a dedicated skill.

#### Scenario: Standalone Execution

- **WHEN** the `ai_content_enricher` skill is executed on a directory of Markdown files
- **THEN** it generates summaries, extracts entities, and creates semantic chunks for each file based on provided flags
- **AND** updates the file content (frontmatter) and/or creates sidecar files

### Requirement: Pydantic AI Integration

The system SHALL use `pydantic-ai` to ensure structured and type-safe AI outputs.

#### Scenario: Model Support

- **WHEN** specific models are requested (e.g., `gpt-4o`, `claude-3-5-sonnet`)
- **THEN** the system correctly maps to the provider strings required by Pydantic AI

#### Scenario: Validation

- **WHEN** the LLM returns data
- **THEN** the system validates it against `SummaryOutput` and `EntityOutput` schemas before saving

### Requirement: Semantic Chunking

The system SHALL support splitting large Markdown documents into semantically meaningful chunks.

#### Scenario: Chunk Generation

- **WHEN** chunking is enabled
- **THEN** the system splits content at header boundaries
- **AND** ensures chunks do not exceed token limits (default 512 tokens)
- **AND** saves chunks as separate files (e.g., `page-chunk-01.md`)

### Requirement: Manifest Integration

The system SHALL update existing manifests with AI-generated metadata.

#### Scenario: Manifest Update

- **WHEN** a `_manifest.json` file exists in the target directory
- **THEN** the system updates it to include new metadata fields (e.g., `summary`, `entities`) for each processed file
