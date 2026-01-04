# Refactor Skill Factory

## Why

The current `spec/skill_factory.py` script generates agent skills that are non-compliant with the new "Agentic Standard" defined in `Agent-Skill-Creator/Full-Skill-Creator-Agent.md` and `openspec/specs/skill-creator/spec.md`.

Specific issues with current output:

- Creates `requirements.txt` (Banned).
- Places python logic in root `{skill_name}.py` instead of `scripts/`.
- Missing `scripts/`, `references/`, and `assets/` directory structure.
- Incorrect SKILL.md frontmatter keys.
- Does not use PEP 723 for dependencies.

## What Changes

We will refactor `spec/skill_factory.py` to become the canonical tool for scaffolding compliant skills.

### Key Changes

1.  **Directory Structure**: Generate `scripts/`, `references/`, and `assets/` folders.
2.  **Manifest**: Generate `SKILL.md` with strict frontmatter (`name`, `description` only) and compliant structure.
3.  **No Banned Files**: Stop generating `requirements.txt` and `__init__.py`.
4.  **PEP 723**: Ensure the generated python script templates use PEP 723 inline script metadata for dependencies.
5.  **Validation**: Ensure the factory output passes the `quick_validate.py` logic defined in the Agent Spec.
