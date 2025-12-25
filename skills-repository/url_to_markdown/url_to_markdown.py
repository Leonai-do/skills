# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "pydantic",
#     "requests",
#     "markdownify",
# ]
# ///
import sys
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional
import typer
from pydantic import BaseModel, Field
import requests
from markdownify import markdownify as md

# --- 1. Define Input Schema ---
class InputModel(BaseModel):
    url: str = Field(..., description="The URL to fetch and convert")

# --- 2. Define Output Schema ---
class OutputModel(BaseModel):
    status: str = Field(..., description="Status of execution: 'success' or 'error'")
    data: Optional[dict] = Field(None, description="Result data on success")
    error: Optional[str] = Field(None, description="Error message on failure")

app = typer.Typer()

def get_filename_from_url(url: str) -> str:
    """Methods to sanitize URL into a filename"""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        path = parsed.netloc
    
    # Replace non-alphanumeric chars with dashes
    slug = re.sub(r'[^a-zA-Z0-9]', '-', path)
    # Remove multiple dashes
    slug = re.sub(r'-+', '-', slug).strip("-")
    
    if not slug:
        slug = "index"
        
    return f"{slug}.md"

@app.command()
def main(
    url: str = typer.Option(..., help="The URL to fetch"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Optional path to save the markdown file"),
    schema: bool = typer.Option(False, help="Print input JSON schema and exit")
):
    """
    Fetches a URL and converts the content to markdown preserving structure
    """

    # --- 3. Schema Discovery ---
    if schema:
        print(InputModel.model_json_schema_json(indent=2))
        return

    # --- 4. Validation ---
    try:
        # Construct the input model to validate args
        inputs = InputModel(url=url)
    except Exception as e:
        # Return structured error to Agent
        print(json.dumps(OutputModel(status="error", error=f"Validation Error: {str(e)}").model_dump()))
        sys.exit(1)

    # --- 5. Business Logic ---
    try:
        print(f"[LOG] Running url_to_markdown with url: {inputs.url}", file=sys.stderr)

        # Use a user agent to avoid being blocked by some sites
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; AntigravityBot/1.0; +http://example.com)"
        }
        response = requests.get(inputs.url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Convert to markdown
        markdown_content = md(response.text, heading_style="ATX")
        
        # --- Automatic Saving Logic ---
        # 1. Determine base directory relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Create domain-based folder: output/domain
        parsed = urlparse(inputs.url)
        domain = parsed.netloc
        # Sanitize domain simple way (replace port colons, etc)
        domain = re.sub(r'[^a-zA-Z0-9.-]', '_', domain)
        
        output_dir = os.path.join(script_dir, "output", domain)
        os.makedirs(output_dir, exist_ok=True)
        
        # 3. Generate filename
        filename = get_filename_from_url(inputs.url)
        save_path = os.path.join(output_dir, filename)
        
        # 4. Save
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print(f"[LOG] Saved markdown to {save_path}", file=sys.stderr)
        
        # Also respect custom output if provided (save a copy or symlink? Just saving copy for now)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"[LOG] Saved copy to {output}", file=sys.stderr)
        
        result = {
            "markdown": markdown_content, 
            "url": inputs.url, 
            "saved_to": save_path
        }

        # --- 6. Success Response ---
        print(json.dumps(OutputModel(status="success", data=result).model_dump()))

    except Exception as e:
        # Graceful error handling
        print(json.dumps(OutputModel(status="error", error=str(e)).model_dump()))
        sys.exit(1)

if __name__ == "__main__":
    app()
