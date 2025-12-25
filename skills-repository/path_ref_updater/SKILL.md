---
name: path-ref-updater
description: Analyzes and fixes broken file path references within a single file across any text-based format.
version: 2.0.0
environment: WSL2/Linux (bash/zsh)
---

# Path Ref Updater

## Description
This skill analyzes a target file (Markdown, HTML, code, documentation, etc.) for broken relative or absolute path references. It searches the project for missing files and updates the file content with correct paths when possible.

**Supported Reference Types:**
- Markdown links: `[text](path)` or `[text](path "title")`
- Markdown images: `![alt](path)` or `![alt](path "title")`
- HTML attributes: `src="path"`, `href="path"` (both single and double quotes)
- Works with any text-based file format (`.md`, `.mdx`, `.html`, `.jsx`, `.tsx`, `.txt`, `.csv`, etc.)

**Safety Guarantees:**
- ✅ Only updates path references within the specified file
- ✅ Never moves, renames, or deletes files
- ✅ Never creates new files
- ✅ Preserves quote styles (single vs double)
- ✅ Preserves path titles and attributes
- ✅ Reports all issues for agent review

---

## Critical Agent Instructions

### ⚠️ MANDATORY: Pre-Execution Checklist

**Before executing this skill, the agent MUST:**

1. **Git Backup (REQUIRED)**
   ```bash
   # Execute in WSL2 terminal - git is NOT available in Windows host
   cd /mnt/d/LeonAI_DO/dev/Agent-Skills  # or appropriate project root
   git add -A
   git commit -m "Backup before path-ref-updater execution on [filename]"
   ```

2. **Identify Project Root**
   - Determine the absolute project root path
   - Convert Windows paths to WSL2 format: `D:\path` → `/mnt/d/path`
   - Use this as `--project-root` parameter

3. **Verify File Context**
   - Read the target file to understand its current path references
   - Note any context about where files SHOULD be located
   - Consider user requirements about specific folders/paths

4. **Understand Reference Context**
   - If file references `../../docs/file.md`, understand the intended structure
   - If multiple `docs` folders exist, determine which one is correct
   - Check if paths are meant to be relative or project-absolute

---

### 🤖 Agent Execution Workflow

#### Step 1: Discovery (Get Schema)
```bash
python3 skills/path_ref_updater/path_ref_updater.py --schema
```

#### Step 2: Dry Run (Recommended First)
```bash
python3 skills/path_ref_updater/path_ref_updater.py \
  --file-path "/mnt/d/project/docs/README.md" \
  --project-root "/mnt/d/project" \
  --dry-run
```

**Agent must analyze dry-run output:**
- Review all "ambiguous" paths - these require manual resolution
- Review all "unfixable" paths - verify they're truly missing
- Confirm "fixed" paths are correct based on project context

#### Step 3: Execute (After Review)
```bash
python3 skills/path_ref_updater/path_ref_updater.py \
  --file-path "/mnt/d/project/docs/README.md" \
  --project-root "/mnt/d/project"
```

#### Step 4: Post-Execution Report
Agent must create a detailed report including:
- Summary of changes made
- List of ambiguous paths requiring manual resolution
- List of unfixable paths (missing files)
- Suggestions for next steps
- Git commit recommendation

---

### 📊 Output Interpretation

The skill returns JSON with this structure:

```json
{
  "status": "success",
  "data": {
    "file": "docs/README.md",
    "message": "Fixed: 3 path(s) | Unfixable: 1 path(s) | Ambiguous: 2 path(s)",
    "changed": true,
    "summary": {
      "total_issues": 6,
      "fixed": 3,
      "unfixable": 1,
      "ambiguous": 2
    },
    "issues": {
      "fixed": [
        {
          "original": "../../old/path/file.md",
          "new": "../correct/path/file.md",
          "status": "fixed",
          "line_number": 15
        }
      ],
      "unfixable": [
        {
          "original": "missing-file.png",
          "status": "unfixable",
          "line_number": 23,
          "context": "File 'missing-file.png' not found in project"
        }
      ],
      "ambiguous": [
        {
          "original": "config.json",
          "status": "ambiguous",
          "line_number": 42,
          "context": "Multiple files found: src/config.json, tests/config.json, docs/config.json"
        }
      ]
    },
    "warnings": [
      "AMBIGUOUS PATHS DETECTED: Multiple files match the filename. Agent must manually determine the correct file based on context."
    ]
  }
}
```

### 🎯 Agent Decision Matrix

| Status | Agent Action Required |
|--------|----------------------|
| **fixed** | ✅ Review and approve. Commit changes if correct. |
| **unfixable** | 🔍 Investigate: Is file truly missing? Typo in path? File deleted? |
| **ambiguous** | ⚠️ **CRITICAL**: Agent must manually determine correct path based on:<br>- File context and purpose<br>- User requirements<br>- Project structure<br>- Semantic meaning of the reference |

---

### 🚨 Common Scenarios & Agent Responses

#### Scenario 1: Multiple `docs` Folders
```
Context: File at `src/components/README.md` references `../../docs/api.md`
Ambiguous Output: Multiple files found: `docs/api.md`, `src/docs/api.md`, `tests/docs/api.md`

Agent Action:
1. Analyze the relative path `../../docs/api.md` from `src/components/`
2. That would resolve to `docs/api.md` (project root level)
3. Manually edit the file to use the correct path
4. Report: "Resolved ambiguous reference to project-level docs folder"
```

#### Scenario 2: Missing File
```
Unfixable: `old-diagram.png` not found

Agent Action:
1. Search project history: `git log --all --full-history -- "**/old-diagram.png"`
2. Check if file was renamed or moved
3. Ask user: "The file old-diagram.png is referenced but missing. Was it renamed or deleted?"
4. If renamed, update manually; if deleted, document and possibly remove reference
```

#### Scenario 3: Cross-Drive Paths (Windows)
```
Error: Cannot calculate relative path (cross-drive?)

Agent Action:
1. Check if files are on different drives (e.g., C: vs D:)
2. In WSL2, both should be accessible via /mnt/
3. Ensure both file and project root are specified as WSL2 paths
4. Re-run with corrected paths
```

#### Scenario 4: Absolute vs Relative Paths
```
Context: File contains `/assets/logo.png` (absolute)

Agent Behavior:
- Treats `/path` as project-root-relative (web-style)
- Resolves to `<project-root>/assets/logo.png`
- If broken, searches for `logo.png` in project
- Updates to relative path from current file

Agent Note: This follows web/documentation conventions where `/` = project root
```

---

## Technical Specifications

### Path Resolution Logic

1. **Valid Paths** (unchanged):
   - External: `http://`, `https://`, `mailto:`, etc.
   - Anchors: `#section-name`
   - Data URIs: `data:image/png;base64,...`

2. **Absolute Paths** (project-root-relative):
   - Path starts with `/` → resolve from `project_root`
   - Example: `/docs/api.md` → `<project-root>/docs/api.md`

3. **Relative Paths**:
   - Path doesn't start with `/` → resolve from current file's directory
   - Example: `../../assets/img.png` → resolve relative to file location

4. **Broken Path Recovery**:
   - Extract filename from broken path
   - Search entire project tree: `root.rglob(filename)`
   - If 1 match: calculate new relative path and fix
   - If 0 matches: report as "unfixable"
   - If 2+ matches: report as "ambiguous" (agent must resolve)

### Encoding & File Type Support

- **Encoding**: UTF-8 only
- **File Types**: Any text-based format
  - Documentation: `.md`, `.mdx`, `.rst`, `.txt`
  - Code: `.js`, `.jsx`, `.ts`, `.tsx`, `.py`, `.html`
  - Data: `.csv`, `.json`, `.yaml`, `.xml`
  - Configuration: `.conf`, `.ini`, `.env`
- **Binary Files**: Will error with encoding message (expected behavior)

---

## Constraints & Limitations

### Hard Constraints
1. ✅ **Single File Only**: Processes exactly one file per execution
2. ✅ **Read-Only Search**: Never modifies files during search phase
3. ✅ **No File Creation**: Never creates missing files
4. ✅ **No File Movement**: Never moves or renames files
5. ✅ **UTF-8 Required**: Binary files will fail gracefully

### Known Limitations
1. **Ambiguous Filenames**: If multiple files share a name, agent must manually resolve
2. **Complex Patterns**: Very unusual reference formats may not be detected
3. **Cross-Drive Paths**: Windows cross-drive relative paths may fail
4. **Order Dependency**: Processes matches in discovery order (not deterministic for multiple matches)

### Agent Responsibilities
- ✅ Git backup before execution
- ✅ Verify project root is correct
- ✅ Analyze dry-run results before committing changes
- ✅ Manually resolve ambiguous paths
- ✅ Document all changes and findings
- ✅ Execute only in WSL2/Linux environment

---

## Usage Examples

### Example 1: Basic Execution
```bash
# 1. Git backup
cd /mnt/d/LeonAI_DO/dev/Agent-Skills
git add -A && git commit -m "Backup before path update"

# 2. Dry run first
python3 skills/path_ref_updater/path_ref_updater.py \
  --file-path "/mnt/d/LeonAI_DO/dev/Agent-Skills/docs/README.md" \
  --project-root "/mnt/d/LeonAI_DO/dev/Agent-Skills" \
  --dry-run

# 3. Review output, then execute
python3 skills/path_ref_updater/path_ref_updater.py \
  --file-path "/mnt/d/LeonAI_DO/dev/Agent-Skills/docs/README.md" \
  --project-root "/mnt/d/LeonAI_DO/dev/Agent-Skills"
```

### Example 2: Handling Ambiguous Output
```bash
# Dry run shows ambiguous paths
{
  "ambiguous": [{
    "original": "config.json",
    "context": "Multiple files found: src/config.json, tests/config.json"
  }]
}

# Agent analysis:
# - File is at src/components/README.md
# - Reference is ../config.json
# - Should resolve to src/config.json (sibling directory)

# Agent action: Manually edit with Desktop Commander
edit_block --file-path /mnt/d/.../README.md \
  --old-string "[config](../config.json)" \
  --new-string "[config](../config.json)"
# (Or use appropriate tool to fix the specific reference)
```

### Example 3: WSL2 Path Conversion
```bash
# Windows path provided by user
User: "Fix paths in D:\Projects\MyApp\docs\api.md"

# Agent converts to WSL2 format
FILE_PATH="/mnt/d/Projects/MyApp/docs/api.md"
PROJECT_ROOT="/mnt/d/Projects/MyApp"

python3 skills/path_ref_updater/path_ref_updater.py \
  --file-path "$FILE_PATH" \
  --project-root "$PROJECT_ROOT"
```

---

## CI/CD Data Gathering

### Agent Reporting Template

After each execution, agent should create a report:

```markdown
## Path Ref Updater Execution Report

**Date**: YYYY-MM-DD HH:MM:SS
**File**: path/to/file.md
**Project Root**: /mnt/d/project

### Summary
- Total Issues: 10
- Fixed Automatically: 7
- Unfixable: 1
- Ambiguous (Manual Resolution Required): 2

### Fixed Paths
| Line | Original | New | Status |
|------|----------|-----|--------|
| 15 | ../../old/path/file.md | ../correct/path/file.md | ✅ Fixed |
| 23 | /assets/old-logo.png | ../assets/logo.png | ✅ Fixed |

### Unfixable Paths
| Line | Path | Reason | Action Taken |
|------|------|--------|--------------|
| 42 | missing-file.png | File not found in project | Investigated git history - file was deleted in commit abc123 |

### Ambiguous Paths (Manual Resolution)
| Line | Path | Candidates | Resolution | Reason |
|------|------|------------|------------|--------|
| 56 | config.json | src/config.json<br>tests/config.json | src/config.json | Reference is from src/components, needs src sibling |
| 89 | docs/api.md | docs/api.md<br>internal/docs/api.md | docs/api.md | User specified project-level docs folder |

### Actions Taken
1. Git backup created: commit hash xyz789
2. Executed dry-run and reviewed all ambiguous paths
3. Manually resolved 2 ambiguous references using edit_block
4. Re-ran skill to fix remaining 7 paths automatically
5. Verified all changes are correct
6. Created final commit: "Fixed broken path references in file.md"

### Constraints Encountered
- None / [List any issues or unexpected behavior]

### Recommendations
- Consider standardizing documentation structure to avoid ambiguous references
- Review if missing-file.png should be restored or reference removed
```

---

## Troubleshooting

### Issue: "File encoding error: not UTF-8"
**Cause**: File is binary or non-UTF-8 encoded
**Solution**: 
- If truly a text file, convert to UTF-8 first
- If binary, this skill cannot process it (expected behavior)

### Issue: "Cannot calculate relative path (cross-drive?)"
**Cause**: File and project root on different Windows drives
**Solution**: 
- Ensure both paths use WSL2 format (`/mnt/d/`, `/mnt/c/`)
- Should not occur in WSL2 environment if paths are correct

### Issue: All paths marked "ambiguous"
**Cause**: Multiple files with same name in project
**Solution**: 
- Agent must manually analyze each reference context
- Use project structure knowledge to determine correct paths
- Consider adding subdirectory to path for clarity

### Issue: "Target file not found"
**Cause**: Path to file is incorrect or file doesn't exist
**Solution**: 
- Verify file path is correct (WSL2 format in Linux environment)
- Check file actually exists: `ls -la /mnt/d/path/to/file.md`
- Use absolute paths for reliability

### Issue: Git not available
**Cause**: Trying to run git in Windows host instead of WSL2
**Solution**: 
- **ALL commands must run in WSL2/Linux terminal**
- Git is only available in WSL2 subsystem
- Convert paths to WSL2 format: `D:\path` → `/mnt/d/path`

---

## Executable Information

**Path**: `skills/path_ref_updater/path_ref_updater.py`
**Python Version**: 3.7+
**Dependencies**: Standard library only (no external packages)
**Environment**: WSL2/Linux (bash or zsh)
**Git Requirement**: Must have git available for backup operations (agent responsibility)

---

## Version History

### v2.0.0 (Current)
- ✅ Added image reference support: `![alt](path)`
- ✅ Enhanced HTML attribute detection (single/double quotes)
- ✅ Complete path context preservation (titles, anchors)
- ✅ Comprehensive issue reporting (fixed, unfixable, ambiguous)
- ✅ Line number tracking for all issues
- ✅ Dry-run mode for safe previewing
- ✅ Detailed agent instructions and decision matrix
- ✅ CI/CD reporting template

### v1.0.0 (Previous)
- Basic Markdown link fixing: `[text](path)`
- Basic HTML attribute fixing: `src="path"`, `href="path"`
- Simple path resolution without detailed reporting

---

## Support & Feedback

For issues, improvements, or questions about this skill:
1. Agent should document all execution results
2. Include full error messages and context
3. Note any edge cases or unexpected behavior
4. Suggest improvements based on real-world usage
