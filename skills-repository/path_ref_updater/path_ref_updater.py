#!/usr/bin/env python3
"""
Path Reference Updater Skill
Analyzes and fixes broken file path references within a single file.
Supports: Markdown links, images, HTML attributes, and any text-based file format.
"""

import sys
import json
import os
import re
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# --- Helper Classes ---
class PathIssue:
    """Represents a path reference issue (fixed or unfixable)"""
    def __init__(self, original: str, new: Optional[str], status: str, 
                 line_number: Optional[int] = None, context: Optional[str] = None):
        self.original = original
        self.new = new
        self.status = status  # "fixed", "unfixable", "ambiguous"
        self.line_number = line_number
        self.context = context
    
    def to_dict(self):
        result = {
            "original": self.original,
            "status": self.status
        }
        if self.new:
            result["new"] = self.new
        if self.line_number:
            result["line_number"] = self.line_number
        if self.context:
            result["context"] = self.context
        return result

def find_all_matching_files(filename: str, root: Path) -> List[Path]:
    """Find all files matching the given filename in the project."""
    matches = []
    for path in root.rglob(filename):
        if path.is_file():
            matches.append(path)
    return matches

def resolve_path(ref_path_str: str, current_file: Path, project_root: Path) -> Tuple[Optional[str], str, Optional[str]]:
    """
    Analyzes a path reference.
    Returns: (new_path, status, context_message)
    - new_path: None if valid or unfixable, corrected path if fixable
    - status: "valid", "fixed", "unfixable", "ambiguous"
    - context_message: Additional info for reporting
    """
    # Ignore external links, anchors, data URIs
    if ref_path_str.startswith(("http://", "https://", "ftp://", "ftps://", 
                                "mailto:", "#", "data:", "javascript:", "tel:")):
        return None, "valid", "External/anchor link"
    
    # Ignore empty paths
    if not ref_path_str.strip():
        return None, "valid", "Empty path"

    # Determine target path - handle both absolute and relative
    is_absolute = ref_path_str.startswith("/")
    
    if is_absolute:
        # Treat /path as project-root-relative (web-style)
        target_path = project_root / ref_path_str.lstrip("/")
    else:
        # Relative to current file
        target_path = current_file.parent / ref_path_str

    # Normalize and check existence
    try:
        target_path = target_path.resolve()
        if target_path.exists():
            return None, "valid", None
    except (ValueError, OSError) as e:
        return None, "unfixable", f"Path resolution error: {str(e)}"

    # Path is broken - try to find the file
    target_filename = Path(ref_path_str).name
    
    # Find all matches
    matches = find_all_matching_files(target_filename, project_root)
    
    if len(matches) == 0:
        return None, "unfixable", f"File '{target_filename}' not found in project"
    
    if len(matches) > 1:
        # Multiple matches found - AGENT must decide
        paths_str = ", ".join([str(p.relative_to(project_root)) for p in matches])
        return None, "ambiguous", f"Multiple files found: {paths_str}"
    
    # Single match found - calculate new relative path
    found_path = matches[0]
    try:
        new_rel_path = os.path.relpath(found_path, current_file.parent)
        return Path(new_rel_path).as_posix(), "fixed", None
    except (ValueError, OSError):
        return None, "unfixable", "Cannot calculate relative path (cross-drive?)"

def extract_path_from_reference(ref_full: str) -> str:
    """
    Extract just the path from a reference that might include titles/attributes.
    Examples:
      - "path/to/file.md" -> "path/to/file.md"
      - "path/to/file.md 'title'" -> "path/to/file.md"
      - "path/to/file.md#anchor" -> "path/to/file.md"
    """
    # Remove anchor
    path = ref_full.split('#')[0]
    # Remove quoted title (common in markdown)
    path = re.split(r'\s+["\']', path)[0]
    return path.strip()

def main():
    parser = argparse.ArgumentParser(
        description="Updates broken path references within files.",
        epilog="Must be executed in WSL2/Linux environment with git available."
    )
    parser.add_argument("--file-path", help="The file to update (absolute or relative)")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--schema", action="store_true", help="Print input JSON schema and exit")
    parser.add_argument("--dry-run", action="store_true", help="Report issues without making changes")
    
    args = parser.parse_args()

    # --- Schema Discovery ---
    if args.schema:
        schema = {
            "title": "PathRefUpdaterInput",
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string", 
                    "description": "The absolute or relative path to the file to update."
                },
                "project_root": {
                    "type": "string", 
                    "default": ".", 
                    "description": "The root of the project to search for missing files."
                },
                "dry_run": {
                    "type": "boolean",
                    "default": False,
                    "description": "If true, report issues without making changes."
                }
            },
            "required": ["file_path"]
        }
        print(json.dumps(schema, indent=2))
        return

    if not args.file_path:
        print(json.dumps({"status": "error", "error": "Missing required argument: --file-path"}))
        sys.exit(1)

    # --- Validation ---
    try:
        target_file = Path(args.file_path).resolve()
        root = Path(args.project_root).resolve()

        if not target_file.exists():
            raise FileNotFoundError(f"Target file not found: {target_file}")
        
        if not target_file.is_file():
            raise ValueError(f"Path is not a file: {target_file}")
        
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Validation Error: {str(e)}"}))
        sys.exit(1)

    # --- Business Logic ---
    try:
        content = target_file.read_text(encoding="utf-8")
        original_content = content
        
        issues = []  # All issues found (fixed, unfixable, ambiguous)
        
        # Regex patterns for different reference types
        # 1. Markdown links: [text](path) or [text](path "title")
        md_link_pattern = re.compile(r'(\[(?:[^\]\\]|\\.)*\])\(([^)]+)\)')
        
        # 2. Markdown images: ![alt](path) or ![alt](path "title")
        md_image_pattern = re.compile(r'(!\[(?:[^\]\\]|\\.)*\])\(([^)]+)\)')
        
        # 3. HTML src attributes (single or double quotes)
        html_src_pattern = re.compile(r'(src\s*=\s*)([\"\'])([^\"\']+)\2', re.IGNORECASE)
        
        # 4. HTML href attributes (single or double quotes)
        html_href_pattern = re.compile(r'(href\s*=\s*)([\"\'])([^\"\']+)\2', re.IGNORECASE)

        new_content = content
        lines = content.split('\n')

        def get_line_number(pos: int) -> int:
            """Get line number from character position."""
            return content[:pos].count('\n') + 1

        def process_match(match, path_group_idx: int, prefix_group_idx: int, 
                          quote_group_idx: Optional[int] = None):
            """Generic processor for any pattern match."""
            nonlocal new_content
            
            full_match = match.group(0)
            prefix = match.group(prefix_group_idx)
            ref_full = match.group(path_group_idx)
            
            # Extract actual path (remove titles, anchors from detection)
            ref_path = extract_path_from_reference(ref_full)
            
            # Resolve the path
            new_path, status, context = resolve_path(ref_path, target_file, root)
            
            # Calculate line number
            line_num = get_line_number(match.start())
            
            # Record issue
            if status != "valid":
                issue = PathIssue(
                    original=ref_path,
                    new=new_path,
                    status=status,
                    line_number=line_num,
                    context=context
                )
                issues.append(issue)
            
            # Replace if fixed (and not dry-run)
            if new_path and not args.dry_run:
                # Preserve quote style for HTML attributes
                if quote_group_idx is not None:
                    quote = match.group(quote_group_idx)
                    replacement = f"{prefix}{quote}{new_path}{quote}"
                else:
                    # Markdown style - preserve any title/attributes after the path
                    suffix = ref_full[len(ref_path):]  # Get everything after the path
                    replacement = f"{prefix}({new_path}{suffix})"
                
                new_content = new_content.replace(full_match, replacement, 1)
                return replacement
            
            return full_match

        # Process all pattern types
        # Note: We process sequentially to maintain order and avoid conflicts
        
        # Markdown images (process before links to avoid conflicts)
        for match in md_image_pattern.finditer(content):
            process_match(match, path_group_idx=2, prefix_group_idx=1)
        
        # Markdown links
        for match in md_link_pattern.finditer(content):
            process_match(match, path_group_idx=2, prefix_group_idx=1)
        
        # HTML src attributes
        for match in html_src_pattern.finditer(content):
            process_match(match, path_group_idx=3, prefix_group_idx=1, quote_group_idx=2)
        
        # HTML href attributes
        for match in html_href_pattern.finditer(content):
            process_match(match, path_group_idx=3, prefix_group_idx=1, quote_group_idx=2)

        # Separate issues by status
        fixed = [i for i in issues if i.status == "fixed"]
        unfixable = [i for i in issues if i.status == "unfixable"]
        ambiguous = [i for i in issues if i.status == "ambiguous"]

        # Write changes if not dry-run
        if new_content != original_content and not args.dry_run:
            target_file.write_text(new_content, encoding="utf-8")
            changed = True
        else:
            changed = False

        # Build response message
        msg_parts = []
        if args.dry_run:
            msg_parts.append("[DRY RUN] No changes made.")
        if fixed:
            msg_parts.append(f"Fixed: {len(fixed)} path(s)")
        if unfixable:
            msg_parts.append(f"Unfixable: {len(unfixable)} path(s)")
        if ambiguous:
            msg_parts.append(f"Ambiguous: {len(ambiguous)} path(s) - AGENT ACTION REQUIRED")
        if not issues:
            msg_parts.append("No broken paths found.")
        
        message = " | ".join(msg_parts)

        # Prepare detailed result
        result = {
            "file": str(target_file.relative_to(root)),
            "message": message,
            "changed": changed,
            "summary": {
                "total_issues": len(issues),
                "fixed": len(fixed),
                "unfixable": len(unfixable),
                "ambiguous": len(ambiguous)
            },
            "issues": {
                "fixed": [i.to_dict() for i in fixed],
                "unfixable": [i.to_dict() for i in unfixable],
                "ambiguous": [i.to_dict() for i in ambiguous]
            }
        }

        # Add warnings for agent
        warnings = []
        if ambiguous:
            warnings.append(
                "AMBIGUOUS PATHS DETECTED: Multiple files match the filename. "
                "Agent must manually determine the correct file based on context."
            )
        if unfixable and not ambiguous:
            warnings.append(
                "UNFIXABLE PATHS: These files do not exist in the project. "
                "Agent should verify if files were moved/deleted or paths are typos."
            )
        
        if warnings:
            result["warnings"] = warnings

        # Success response
        print(json.dumps({"status": "success", "data": result}, indent=2))

    except UnicodeDecodeError:
        print(json.dumps({
            "status": "error", 
            "error": f"File encoding error: {target_file} is not UTF-8. Binary or unsupported encoding."
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
