## ADDED Requirements

### Requirement: Path Reference Correction
The skill MUST identify and correct broken or incorrect file path references within a target file.

#### Scenario: Fix broken relative link
- **WHEN** a Markdown file contains `[Link](../bad/path/file.md)`
- **AND** the actual file exists at `../../correct/path/file.md`
- **THEN** the skill updates the content to `[Link](../../correct/path/file.md)`

### Requirement: Immutable File Structure
The skill MUST NOT move, rename, delete, or create files in the file system. It SHALL ONLY modify the contents of the target file.

#### Scenario: File remains in place
- **WHEN** the skill processes `/src/utils/helper.py`
- **THEN** `/src/utils/helper.py` remains at that exact path
- **AND** its internal imports are updated

### Requirement: Single File Processing
The skill MUST process exactly one file per execution context to ensure granular control.

#### Scenario: Single target
- **WHEN** invoked with target `doc.md`
- **THEN** only `doc.md` is read and modified
