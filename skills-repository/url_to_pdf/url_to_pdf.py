# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "pydantic",
#     "playwright",
# ]
# ///
import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import typer
from pydantic import BaseModel, Field
from playwright.sync_api import sync_playwright, Error as PlaywrightError

# --- 1. Define Input Schema ---
class InputModel(BaseModel):
    url: str = Field(..., description="The URL to download as PDF")
    output_name: Optional[str] = Field(None, description="Custom name for the output file (without extension)")

# --- 2. Define Output Schema ---
class OutputModel(BaseModel):
    status: str = Field(..., description="Status of execution: 'success' or 'error'")
    output_path: Optional[str] = Field(None, description="Path where PDF was saved")
    error: Optional[str] = Field(None, description="Error message on failure")

app = typer.Typer()

def get_output_dir() -> Path:
    """Returns the daily output directory."""
    today = datetime.now().strftime("%Y-%m-%d")
    base_dir = Path(__file__).parent / "output" / today
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def sanitize_filename(name: str) -> str:
    """Sanitizes a string to be safe for filenames."""
    # Keep alphanumeric, dashes, underscores, and periods
    return "".join(c for c in name if c.isalnum() or c in "._-")

@app.command()
def main(
    url: str = typer.Option(..., help="The URL to download"),
    name: str = typer.Option(None, help="Custom output filename (optional)"),
    schema: bool = typer.Option(False, help="Print input JSON schema and exit")
):
    """
    Downloads a URL and saves it as a PDF file using Playwright.
    """

    # --- 3. Schema Discovery ---
    if schema:
        print(InputModel.model_json_schema_json(indent=2))
        return

    # --- 4. Validation ---
    try:
        inputs = InputModel(url=url, output_name=name)
    except Exception as e:
        print(json.dumps(OutputModel(status="error", error=f"Validation Error: {str(e)}").model_dump()))
        sys.exit(1)

    # --- 5. Business Logic ---
    try:
        print(f"[LOG] Generating PDF for: {inputs.url}", file=sys.stderr)
        
        output_dir = get_output_dir()
        
        # Determine filename
        if inputs.output_name:
            filename = sanitize_filename(inputs.output_name)
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
        else:
            # Generate from URL or timestamp
            timestamp = datetime.now().strftime("%H%M%S")
            # distinct filename
            filename = f"webpage_{timestamp}.pdf"
            
        output_path = output_dir / filename

        # Playwright execution
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(inputs.url, wait_until="networkidle")
                page.pdf(path=str(output_path), format="A4")
                browser.close()
        except PlaywrightError as pe:
            # Verify if it's a browser missing error
            if "Executable doesn't exist" in str(pe):
                print(f"[ERROR] Browser not found. Attempting to install...", file=sys.stderr)
                # Attempt to provide instructions or handle it? 
                # Since we are inside a python script, we can't easily run 'playwright install' 
                # effectively if we rely on the uv venv logic outside, but we can try subprocess.
                import subprocess
                subprocess.run(["playwright", "install", "chromium"], check=True)
                
                # Retry once
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(inputs.url, wait_until="networkidle")
                    page.pdf(path=str(output_path), format="A4")
                    browser.close()
            else:
                raise pe

        # --- 6. Success Response ---
        print(json.dumps(OutputModel(
            status="success", 
            output_path=str(output_path)
        ).model_dump()))

    except Exception as e:
        print(json.dumps(OutputModel(status="error", error=str(e)).model_dump()))
        sys.exit(1)

if __name__ == "__main__":
    app()
