# Proposal: Formalize New Skill Creator Agent

## Why

The "New Skill Creator Agent" introduced a suite of new skills and a standardized framework for skill creation (`global-skill_creator.md`). However, these assets currently reside in a detached `New Skill Creator Agent` directory, separated from the main `skills/` library and the OpenSpec standards.

To fully leverage these capabilities, we must integrate them into the core repository structure, formally define the "Skill Creator" as an OpenSpec capability, and ensure all new skills are properly indexed and available to the agent. This change addresses the "AD" (Added-Deleted) git status discrepancy by properly restoring and cataloging these files.

## What Changes

### Structural Changes

- **Merge Skills**: Move all skills from `New Skill Creator Agent/skills/` to the root `skills/` directory.
- **Integrate Docs**: Move `New Skill Creator Agent/docs` and `global-skill_creator.md` to `docs/skills/` to serve as the unified documentation for the Skill System.
- **Cleanup**: Remove the temporary `New Skill Creator Agent` directory.

### OpenSpec Formalization

- **Define Capability**: Establish `skill-creator` as a formal OpenSpec capability in `openspec/specs/skill-creator/spec.md`.
- **Register Skills**: Ensure all moved skills are recognized by the system (implicitly via the `skills/` directory presence).

### New Capabilities

The following skills will be formally available:

- `skill-creator` (The meta-skill for building skills)
- `algorithmic-art`
- `brand-guidelines`
- `canvas-design`
- `doc-coauthoring`
- `docx`
- `frontend-design`
- `internal-comms`
- `mcp-builder`
- `pdf`
- `pptx`
- `slack-gif-creator`
- `theme-factory`
- `url_to_markdown`
- `url_to_pdf`
- `web-artifacts-builder`
- `webapp-testing`
- `xlsx`
