# Design: Skill Creator System

## Architecture

The Skill Creator system provides a standardized way to extend the agent's capabilities. It consists of:

1.  **Skill Library (`skills/`)**: A collection of self-contained skills.

    - Each skill has a `SKILL.md` defining its interface.
    - Optional `scripts/` (python/bash/etc) for execution.
    - Optional `assets/` and `references/`.

2.  **Skill Factory (`skill_factory.py`)**: A script to scaffold new skills.

    - Located in `skills/skill-creator/` (proposed move).
    - Usage: `python tools/skill_factory.py "{name}" "{description}"`

3.  **Documentation (`docs/skills/`)**:
    - `GUIDE.md`: The overarching guide for creating skills (formerly `global-skill_creator.md`).
    - Research naming conventions and structural rules (PEP 723, etc.).

## Integration with OpenSpec

The "Skill Creator" itself is treated as a core capability. The individual skills are "tools" or "modules" provided by this capability. By formalizing this structure, we ensure that new skills are created consistently and are discoverable.
