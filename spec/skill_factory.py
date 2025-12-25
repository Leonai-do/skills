# tools/skill_factory.py
import os
import sys
import argparse
import textwrap
import json

def create_skill(name, description):
    """
    Creates a new agent skill adhering to the Antigravity High-Context Standard.
    Stack: Typer (CLI) + Pydantic (Validation/Schema).
    
    Structure:
      skills/{name}/
      ├── SKILL.md          (Manifest & Instructions)
      ├── requirements.txt  (Dependencies)
      ├── __init__.py       (Package marker)
      └── {name}.py         (Executable logic)
    """
    
    # Normalize skill name (snake_case for folders/scripts)
    safe_name = name.lower().replace(" ", "_").replace("-", "_")
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")
    skill_dir = os.path.join(base_dir, safe_name)
    
    # 1. Create Directory
    if os.path.exists(skill_dir):
        print(f"Error: Skill '{safe_name}' already exists at {skill_dir}")
        return
    
    os.makedirs(skill_dir)
    with open(os.path.join(skill_dir, "__init__.py"), "w") as f:
        f.write("")
    
    # 2. Create SKILL.md (The Manifest)
    # This uses the standard YAML frontmatter + Markdown body
    manifest_content = textwrap.dedent(f"""\
        ---
        name: {safe_name}
        description: {description}
        schema_source: {safe_name}.py
        ---
        # {name.replace('_', ' ').title()}

        ## Description
        {description}

        ## Usage
        This skill is a self-documenting CLI tool.
        
        ### Discovery
        Get the JSON schema for inputs:
        ```bash
        python tools/skills/{safe_name}/{safe_name}.py --schema
        ```

        ### Execution
        ```bash
        python tools/skills/{safe_name}/{safe_name}.py --query "input"
        ```

        ## Executable
        Path: `tools/skills/{safe_name}/{safe_name}.py`
        """)
    
    with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
        f.write(manifest_content)

    # 3. Create requirements.txt
    reqs_content = "typer\npydantic\n"
    with open(os.path.join(skill_dir, "requirements.txt"), "w") as f:
        f.write(reqs_content)

    # 4. Create the Typer+Pydantic Script Template
    script_content = textwrap.dedent(f"""\
        import sys
        import json
        from typing import Optional
        import typer
        from pydantic import BaseModel, Field

        # --- 1. Define Input Schema ---
        class InputModel(BaseModel):
            query: str = Field(..., description="The main input for the skill")
            # TODO: Add more fields here as needed
            # limit: int = Field(5, description="Example parameter")

        # --- 2. Define Output Schema ---
        class OutputModel(BaseModel):
            status: str = Field(..., description="Status of execution: 'success' or 'error'")
            data: Optional[dict] = Field(None, description="Result data on success")
            error: Optional[str] = Field(None, description="Error message on failure")

        app = typer.Typer()

        @app.command()
        def main(
            query: str = typer.Option(..., help="The main input query"),
            # TODO: Add matching arguments here
            schema: bool = typer.Option(False, help="Print input JSON schema and exit")
        ):
            \"\"\"
            {description}
            \"\"\"
            
            # --- 3. Schema Discovery ---
            if schema:
                print(InputModel.model_json_schema_json(indent=2))
                return

            # --- 4. Validation ---
            try:
                # Construct the input model to validate args
                inputs = InputModel(query=query)
            except Exception as e:
                # Return structured error to Agent
                print(json.dumps(OutputModel(status="error", error=f"Validation Error: {{str(e)}}").model_dump()))
                sys.exit(1)

            # --- 5. Business Logic ---
            try:
                print(f"[LOG] Running {safe_name} with query: {{inputs.query}}", file=sys.stderr)
                
                # TODO: Implement your logic here
                # result = do_something(inputs.query)
                result = {{"message": "Hello from {safe_name}", "received": inputs.query}}
                
                # --- 6. Success Response ---
                print(json.dumps(OutputModel(status="success", data=result).model_dump()))
                
            except Exception as e:
                # Graceful error handling
                print(json.dumps(OutputModel(status="error", error=str(e)).model_dump()))
                sys.exit(1)

        if __name__ == "__main__":
            app()
        """)
        
    with open(os.path.join(skill_dir, f"{safe_name}.py"), "w") as f:
        f.write(script_content)

    print(f"✅ Skill '{safe_name}' created successfully at {skill_dir}/")
    print(f"Stack: Typer + Pydantic")
    print(f"Action: Implement logic in skills/{safe_name}/{safe_name}.py")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold a new Agent Skill (Typer+Pydantic).")
    parser.add_argument("name", help="The unique name of the skill (e.g., 'git_audit')")
    parser.add_argument("description", help="What this skill does (for the Agent's context)")
    args = parser.parse_args()
    
    create_skill(args.name, args.description)