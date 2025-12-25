# Report: Path Ref Updater Skill Creation
**Date:** 2025-12-25

## Initial State
The project lacked a specialized tool for automatically fixing broken file path references without altering the file structure.

## Changes Made
- **Created Skill:** `skills/path_ref_updater`
    - Implemented `path_ref_updater.py` using `typer` and `pydantic`.
    - Logic: Scans Markdown/HTML files for links/src/href, validates against project files, and updates paths if broken but findable.
    - Constraints: Non-destructive (no moves/renames), single file scope.
- **OpenSpec:**
    - Created change `add-path-ref-updater`.
    - Defined spec `specs/path-ref-updater/spec.md`.
    - Archived change.

## User Request
"Let's load and embody the "Skill Creator Agent" to create an skill that updates all path references inside each file to be corect, 1 file at at time, this skill will not modify the folder and file structure nor move any files to another location, it will only plan how to modify and update the contents of each file to point to the actual path of each file in the given project so all paths are always updated."

## Reference: SKILL.md
```markdown
---
name: path-ref-updater
description: Analyzes and fixes broken file path references within a single file.
---
# Path Ref Updater

## Description
This skill analyzes a target file (Markdown, HTML, etc.) for broken relative or absolute path references. It searches the project for the missing files and, if found, updates the file content with the correct path.

**Scope:**
- Fixes Markdown links: `[text](path)`
- Fixes HTML attributes: `src="path"`, `href="path"`
- **NEVER** moves, renames, or deletes files.
- **NEVER** creates new files.

## Usage

### 1. Discovery
Get the input schema:
```bash
python3 skills/path_ref_updater/path_ref_updater.py --schema
```

### 2. Execution
Run against a specific file:
```bash
python3 skills/path_ref_updater/path_ref_updater.py --file-path "path/to/doc.md" --project-root "."
```
```
