# Agent Skills Project Context

## Project Overview
This repository contains **Agent Skills** for Claude and the Antigravity system. Skills are specialized capabilities (instructions + scripts) that agents can dynamically load to perform specific tasks, such as document editing, data analysis, or creative generation.

## Environment & Tools
- **OS:** Linux (WSL2 compatible)
- **Language:** Python 3.x
- **Key Dependencies:** `typer`, `pydantic` (for skill scripts)

### Core Utilities
- **`skill_factory.py`**: The primary CLI tool for scaffolding new skills.
  - Usage: `python skill_factory.py "skill_name" "Description of skill"`
  - Generates a folder with `SKILL.md`, `requirements.txt`, and a Python script template.

- **`openspec`**: The standard tool for managing project specifications and change proposals.
  - See `openspec/AGENTS.md` for detailed instructions on the planning workflow.

## Directory Structure
- **`skills-repository/`**: The main collection of existing skills (e.g., `docx`, `pdf`, `algorithmic-art`).
  - Each skill is a self-contained directory with a `SKILL.md` manifest.
- **`Agent-Skill-Creator/`**: Contains resources and definitions for agents specialized in creating other skills.
- **`openspec/`**: Contains the project's specifications (`specs/`) and active change proposals (`changes/`).
- **`spec/`**: Contains the broader `agent-skills-spec.md`.
- **`template/`**: Holds the standard `SKILL.md` template for new skills.

## Workflows

### 1. Creating a New Skill
To add a new capability:
1.  Run `python skill_factory.py <name> <description>`.
2.  Implement the logic in the generated `skills/<name>/<name>.py`.
3.  Define the interface and instructions in `skills/<name>/SKILL.md`.

### 2. Managing Changes (OpenSpec)
For any significant change (new feature, architectural shift, breaking change):
1.  **Plan:** Create a proposal using `openspec` in `openspec/changes/<change-id>/`.
2.  **Scaffold:** Create `proposal.md`, `tasks.md`, and spec deltas.
3.  **Implement:** Follow the `tasks.md` checklist.
4.  **Archive:** Use `openspec archive` to finalize the change.

**Note:** Always consult `openspec/AGENTS.md` when engaging in planning or architectural work.

## conventions
- **Naming:** Skills use `kebab-case` for folders and `snake_case` for Python scripts.
- **Manifest:** Every skill MUST have a `SKILL.md` with valid YAML frontmatter (`name`, `description`).
- **Self-Documenting:** Skill scripts should support a `--schema` flag to output their input JSON schema.
