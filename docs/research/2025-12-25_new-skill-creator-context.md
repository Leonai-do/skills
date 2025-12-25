# Research: New Skill Creator Agent Context

**Date**: 2025-12-25
**Context**: Researching the necessary information to document the creation of a new AI Agent specialized in creating skills, ensuring it understands the structure, architecture, tools, and constraints of the project.

## Executive Summary

The "New Skill Creator Agent" context is fully defined within the existing `skills/skill-creator` skill. This skill serves as the "System Prompt" or "Motherboard" for an agent dedicated to creating other skills.

To create the New Skill Creator Agent, we must provide it with the **Authoritative Spec** found in `skills/skill-creator/SKILL.md` and its associated references. This spec allows the agent to replicate the standard skill structure, adhering to the project's strict constraints on conciseness and context management.

## Key Constraints & Architecture

Based on `skills/skill-creator/SKILL.md`, the following rules are non-negotiable for new skills:

### 1. Anatomy of a Skill

Every skill MUST follow this directory structure:

```
unique-skill-name/
├── SKILL.md (Required: Entry point)
│   ├── Frontmatter (YAML: name, description)
│   └── Body (Markdown: Instructions)
└── Bundled Resources (Optional)
    ├── scripts/ (Executable code)
    ├── references/ (Docs loaded on demand)
    └── assets/ (Static files for output)
```

### 2. Progressive Disclosure Principle

Skills must respect the context window as a public good.

1.  **Metadata** (`name`, `description`): Always loaded. Must be concise.
2.  **Body** (`SKILL.md`): Loaded only on trigger. Keep < 500 lines.
3.  **Resources**: Loaded/Executed only when specifically needed.

### 3. "No Auxiliaries" Rule

Do NOT create `README.md`, `INSTALL.md`, or `CHANGELOG.md` inside a skill. The skill should only contain what the _Agent_ needs to do the job.

### 4. Tooling

The project provides standard scripts that the Agent should know about and use:

- `scripts/init_skill.py`: Generates the template structure.
- `scripts/package_skill.py`: Validates and zips the skill.

## External Research & Gap Analysis

To operationalize the "Skill Creator" as an autonomous agent, we identified gaps in the internal documentation regarding _agentic_ behavior. Deep research provided the following solutions:

### 1. The "Meta-Agent" Architecture

Research into "Recursive Self-Improvement" and "Context Engineering" suggests a specific architecture for the Skill Creator Agent:

- **Role**: The Agent must be explicitly prompted as an "Architect" or "Tool Builder", distinct from a "User". This prevents "Context Pollution" where the agent might confuse the instructions it is _writing_ with instructions it should _follow_.
- **Workflow**: A "Generate -> Critique -> Revise" loop is essential.
  1.  **Plan**: Define the skill's purpose and necessary resources.
  2.  **Init**: Run `init_skill.py`.
  3.  **Draft**: Write `SKILL.md` and resources.
  4.  **Critique**: _Read back_ the generated files and validate them against `skills/skill-creator/SKILL.md` constraints (unbounded context warnings, conciseness checks).
  5.  **Revise**: Fix issues found in critique.
  6.  **Package**: Run `package_skill.py`.

### 2. Preventing Hallucinations in Documentation

AI-generated documentation often suffers from verbosity or hallucinated APIs.

- **Solution**: "Grounding via RAG". The Skill Creator must _read_ the source code or authoritative docs of the tool it is wrapping before writing the skill. It cannot just "know" the API.
- **Constraint**: Enforce "No Auxiliaries" strictly. The Agent should be penalized (in its system prompt or critique phase) for creating `README.md` or other fluff.

### 3. Progressive Disclosure Implementation

- **Constraint**: The `SKILL.md` body is limited to <500 lines.
- **Pattern**: The Agent should automatically split content into `references/` if the draft exceeds this limit. This logic should be hardcoded into the agent's operating procedure.

### 4. Tooling Gaps Filled

- **Gap**: `init_skill.py` creates "TODO" placeholders.
- **Fix**: The Agent's Definition of Done (DoD) must explicitly state "No 'TODO' strings remain in any file". This is a simple but critical automated check.

## RULES for Skill Creation

The following Hard-Coded Guidelines must be adhered to by the Skill Creator Agent:

1.  **Mandatory Init**: ALWAYS start by running `python scripts/init_skill.py <skill-name>` to generate the canonical structure. **NEVER** manually create the folder structure.
2.  **No TODOs Allowed**: The Agent is NOT DONE until every `TODO`, `[INSERT]`, or placeholder text in `SKILL.md` and generated scripts is replaced with actual, functional content or deleted.
3.  **Strict File Sandbox**:
    - **ALLOWED**: `SKILL.md`, `scripts/*.py`, `references/*.md`, `assets/*`
    - **BANNED**: `README.md`, `LICENSE` (unless referencing root), `requirements.txt` (dependencies should be standard or bundled), `.gitignore`.
4.  **Conciseness Prime Directive**:
    - If `SKILL.md` > 500 lines -> EXTRACT sections to `references/`.
    - If a reference > 1000 lines -> SUMMARIZE it or use `grep` patterns.
5.  **Self-Verification Required**:
    - After writing files, run `python scripts/package_skill.py <skill-name>`.
    - If it fails validation, FIX the errors and try again.
    - If it passes, the task is complete.
6.  **Persona Integrity**: You are building a tool for _another AI_. Do not write for humans ("Welcome to this skill!"). Write for the machine ("Action: Execute script...").
7.  **Execution-First**: Prefer Python scripts (`scripts/`) over text instructions for anything deterministic (math, file conversion, API calls).
8.  **Reference-First**: Prefer reference files (`references/`) over long text instructions for static knowledge (API docs, company policies).

## Context Data for the Agent

To "bootstrap" the New Skill Creator Agent, the following files constitute its necessary knowledge base:

1.  **`skills/skill-creator/SKILL.md`**: The core logic and philosophy.
2.  **`skills/skill-creator/references/workflows.md`**: Design patterns for sequential and conditional workflows.
3.  **`skills/skill-creator/references/output-patterns.md`**: Templates for high-quality output.
4.  **`template/SKILL.md`**: The raw template it will populating (or using the init script).

## Action Plan

- [ ] **Formalize**: Use the content of `skills/skill-creator` to define the `skill-creator` OpenSpec capability.
- [ ] **Integration**: Ensure the `init_skill.py` script is available in the agent's environment or that the agent knows how to write the files manually if the script is absent (though using the script is preferred).
- [ ] **Validation**: The agent should use `package_skill.py` logic (or the script itself) to self-verify its creations.
