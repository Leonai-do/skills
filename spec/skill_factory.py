# tools/skill_factory.py
import os
import sys
import argparse
import textwrap
from pathlib import Path

# --- Templates ---

SKILL_TEMPLATE = """---
name: {skill_name}
description: {description}
---

# {skill_title}

## Overview

{description}

## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose. Common patterns:

**1. Workflow-Based** (best for sequential processes)
- Works well when there are clear step-by-step procedures
- Example: DOCX skill with "Workflow Decision Tree" -> "Reading" -> "Creating" -> "Editing"
- Structure: ## Overview -> ## Workflow Decision Tree -> ## Step 1 -> ## Step 2...

**2. Task-Based** (best for tool collections)
- Works well when the skill offers different operations/capabilities
- Example: PDF skill with "Quick Start" -> "Merge PDFs" -> "Split PDFs" -> "Extract Text"
- Structure: ## Overview -> ## Quick Start -> ## Task Category 1 -> ## Task Category 2...

**3. Reference/Guidelines** (best for standards or specifications)
- Works well for brand guidelines, coding standards, or requirements
- Example: Brand styling with "Brand Guidelines" -> "Colors" -> "Typography" -> "Features"
- Structure: ## Overview -> ## Guidelines -> ## Specifications -> ## Usage...

**4. Capabilities-Based** (best for integrated systems)
- Works well when the skill provides multiple interrelated features
- Example: Product Management with "Core Capabilities" -> numbered capability list
- Structure: ## Overview -> ## Core Capabilities -> ### 1. Feature -> ### 2. Feature...

Patterns can be mixed and matched as needed. Most skills combine patterns (e.g., start with task-based, add workflow for complex operations).

Delete this entire "Structuring This Skill" section when done - it's just guidance.]

## [TODO: Replace with the first main section based on chosen structure]

[TODO: Add content here. See examples in existing skills:
- Code samples for technical skills
- Decision trees for complex workflows
- Concrete examples with realistic user requests
- References to scripts/templates/references as needed]

## Resources

This skill includes example resource directories that demonstrate how to organize different types of bundled resources:

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Claude for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Claude's process and thinking.

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Claude should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Claude produces.

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Any unneeded directories can be deleted.** Not every skill requires all three types of resources.
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
# /// script
# dependencies = [
#   "typer",
# ]
# ///
"""
Example helper script for {skill_name}
This uses PEP 723 for inline dependency declaration.
"""

import typer

app = typer.Typer()

@app.command()
def main(name: str):
    print(f"Hello {{name}}")

if __name__ == "__main__":
    app()
'''

EXAMPLE_REFERENCE = """# Reference Documentation for {skill_title}

This is a placeholder for detailed reference documentation.
Replace with actual reference content or delete if not needed.

## When Reference Docs Are Useful

Reference docs are ideal for:
- Comprehensive API documentation
- Detailed workflow guides
- Complex multi-step processes
- Information too lengthy for main SKILL.md
- Content that's only needed for specific use cases
"""

EXAMPLE_ASSET = """# Example Asset File

This placeholder represents where asset files would be stored.
Replace with actual asset files (templates, images, fonts, etc.) or delete if not needed.

Asset files are NOT intended to be loaded into context, but rather used within
the output Claude produces.

## Common Asset Types

- Templates: .pptx, .docx, boilerplate directories
- Images: .png, .jpg, .svg, .gif
- Fonts: .ttf, .otf, .woff, .woff2
- Boilerplate code: Project directories, starter files
- Icons: .ico, .svg
- Data files: .csv, .json, .xml, .yaml
"""


def title_case_skill_name(skill_name):
    """Convert hyphenated skill name to Title Case for display."""
    return ' '.join(word.capitalize() for word in skill_name.split('-'))


def create_skill(name: str, description: str, base_path: str = "skills"):
    """
    Creates a new agent skill adhering to the OpenSpec Agentic Standard.
    """
    
    # Normalize skill name (kebab-case preferred in new spec, but we handle safe naming)
    safe_name = name.lower().replace(" ", "-").replace("_", "-")
    
    # Determine skill directory path
    # If base_path is absolute, use it. Otherwise join with current cwd or __file__ logic.
    # We'll default to creating in the 'skills' folder relative to CWD if not specified, 
    # but the tool usually runs from root.
    
    # Logic to find the 'skills' directory relative to this script if base_path is generic
    if base_path == "skills":
         # Try to find a 'skills' folder in the project root first
         project_root = Path(__file__).resolve().parent.parent
         skill_dir = project_root / "skills" / safe_name
    else:
         skill_dir = Path(base_path) / safe_name

    # Check if directory already exists
    if skill_dir.exists():
        print(f"❌ Error: Skill directory already exists: {skill_dir}")
        return

    # Create skill directory
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"✅ Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        return

    # Create SKILL.md
    skill_title = title_case_skill_name(safe_name)
    skill_content = SKILL_TEMPLATE.format(
        skill_name=safe_name,
        skill_title=skill_title,
        description=description
    )

    skill_md_path = skill_dir / 'SKILL.md'
    try:
        skill_md_path.write_text(skill_content)
        print("✅ Created SKILL.md")
    except Exception as e:
        print(f"❌ Error creating SKILL.md: {e}")
        return

    # Create resource directories
    try:
        # scripts/
        scripts_dir = skill_dir / 'scripts'
        scripts_dir.mkdir(exist_ok=True)
        example_script = scripts_dir / 'example.py'
        example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=safe_name))
        example_script.chmod(0o755)
        print("✅ Created scripts/example.py (PEP 723)")

        # references/
        references_dir = skill_dir / 'references'
        references_dir.mkdir(exist_ok=True)
        example_reference = references_dir / 'api_reference.md'
        example_reference.write_text(EXAMPLE_REFERENCE.format(skill_title=skill_title))
        print("✅ Created references/api_reference.md")

        # assets/
        assets_dir = skill_dir / 'assets'
        assets_dir.mkdir(exist_ok=True)
        example_asset = assets_dir / 'example_asset.txt'
        example_asset.write_text(EXAMPLE_ASSET)
        print("✅ Created assets/example_asset.txt")

    except Exception as e:
        print(f"❌ Error creating resource directories: {e}")
        return

    print(f"\n✅ Skill '{safe_name}' scaffolded successfully at {skill_dir}/")
    print(f"Action: Edit SKILL.md to define logic, and implement scripts in scripts/.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold a new Agent Skill (OpenSpec Standard).")
    parser.add_argument("name", help="The unique name of the skill (e.g., 'git-audit')")
    parser.add_argument("description", help="What this skill does (for the Agent's context)")
    parser.add_argument("--path", default="skills", help="Base path for skills (default: ./skills)")
    
    args = parser.parse_args()
    
    create_skill(args.name, args.description, args.path)