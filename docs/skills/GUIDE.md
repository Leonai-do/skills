---
description: Creates new capabilities and tools for the agent by generating file structures and boilerplate code.
---

# Skill Creator

## Description

Use this skill when the user asks you to "learn" a new task, "create a tool," or "build a skill." This skill creates the standardized folder structure required for you to use the new capability later.

## Rules (Mandatory)

These rules are non-negotiable for the Skill System.

### 1. Modern Execution (PEP 723 / uv)

- **DO**: Use `uv run` to execute scripts.
- **DO**: Include **PEP 723** metadata header at the top of every python script:
  ```python
  # /// script
  # requires-python = ">=3.11"
  # dependencies = [
  #     "typer",
  #     "pydantic",
  #     # ... other libs
  # ]
  # ///
  import sys
  ```
- **DON'T**: Use `pip install` manually. Let `uv` handle dependencies via the header.

### 2. File Organization

- **Root Path**: All skills live in `tools/skills/{skill_name}/`.
- **Output**: All file outputs (reports, downloads) MUST be saved in:
  `tools/skills/{skill_name}/output/{YYYY-MM-DD}/`
- **Structure**:
  ```
  tools/skills/my_skill/
  ├── my_skill.py      # Executable entry point
  ├── SKILL.md         # Documentation
  ├── output/          # All generated artifacts
  │   └── 2025-01-01/
  └── .gitignore
  ```

### 3. Git Management

- **DO**: Commit skills to the main repository.
- **DO**: Always create a **feature branch** (e.g., `feat/skill-{name}`) before starting work. **NEVER** commit directly to `main`.
- **DON'T**: create nested git repositories (do NOT run `git init` inside a skill folder). The skills are part of the `global_workflows` repo.

## Instructions

1.  **Identify**: Extract the `skill_name` (short, snake_case) and `description`.
2.  **Scaffold**: Run the factory script to generate the files.
    ```bash
    python tools/skill_factory.py "{skill_name}" "{description}"
    ```
3.  **Implement**:
    - Read the file: `tools/skills/{skill_name}/{skill_name}.py`
    - **ADD THE PEP 723 HEADER** (copy dependencies from `requirements.txt` to the header).
    - **CLEANUP**: Delete `requirements.txt` once dependencies are in the header.
    - **IMPLEMENT AUTO-SAVE**: Add logic to save any file output to `output/YYYY-MM-DD/`.
    - **DOCUMENT**: Update `SKILL.md` with the final `uv run` command, parameters, and examples.
    - Rewrite the logic to perform the task.
4.  **Verify**:
    - Run the help command:
      ```bash
      uv run tools/skills/{skill_name}/{skill_name}.py --help
      ```
    - Run a test execution.
5.  **Save**:
    - Create a branch: `git checkout -b feat/skill-{skill_name}`
    - Commit changes: `git commit -m "feat: add {skill_name} skill"`
    - (Optional) Push to remote if configured.

## Constraints

- Always use snake_case for the skill name.
- Do not create a skill if one with the same name already exists.

---

# Antigravity Workspace Configuration

## Skill System

- **Location**: `tools/skills/`
- **Execution**: `uv run tools/skills/{name}/{name}.py`

---

## Workflow Demo

**User:**

> /agent Create a new skill called "currency_converter" that fetches exchange rates.

**Antigravity Agent (Action):**

```bash
python tools/skill_factory.py "currency_converter" "Fetches exchange rates"
```

**System Output:**

> ✅ Skill 'currency_converter' created successfully at tools/skills/currency_converter/

**Antigravity Agent (Implementation):**

1.  Add PEP 723 header to `currency_converter.py`.
2.  Import `requests` and add to dependencies list.
3.  Add logic to save results to `output/DATE/rates.json`.

**Antigravity Agent (Verification):**

```bash
uv run tools/skills/currency_converter/currency_converter.py --input 100
```
