# Change: Add Path Reference Updater Skill

## Why
In large projects, file path references (imports, markdown links, asset paths) often break or become outdated. Manually verifying and fixing these paths is tedious and error-prone. We need a specialized skill to automate the validation and correction of these paths within existing files, ensuring data integrity without altering the project's directory structure.

## What Changes
- Create a new skill `path-ref-updater`.
- This skill will:
    - Analyze a target file for path references.
    - Verify the existence of referenced files.
    - Calculate correct relative or absolute paths.
    - Update the *content* of the file with correct paths.
    - strictly **NEVER** move, rename, or delete the file itself.

## Impact
- **New Capability**: `skills/path-ref-updater`
- **Affected Specs**: `specs/path-ref-updater/spec.md` (New)
