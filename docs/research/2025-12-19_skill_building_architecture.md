# Research: AI Agent Skill Architecture & Implementation Best Practices

**Date**: 2025-12-19
**Context**: Result of `@[/openspec-deep-research]` triggered to improve the `skill_creator` agent and define a standard for building robust, modular AI tasks.

## Executive Summary

To build scalable and reliable "Skills" (executable tools) for AI Agents, we must move beyond ad-hoc Python scripts to a **Structured CLI Architecture**. The "Gold Standard" implementation pattern for Python-based agent skills combines **Typer** (for CLI experience) and **Pydantic** (for data validation and schema generation).

**Key Recommendations:**

1.  **Strict Interfaces**: Skills must define inputs/outputs using Pydantic Models.
2.  **Self-Documentation**: Every skill should implement a `--schema` command that outputs its input JSON schema. This allows Agents to auto-discover how to use the tool correctly.
3.  **Structured Error Handling**: Errors must be caught and returned as structured JSON (to stdout) rather than crashing with a traceback (to stderr), enabling the Agent to "catch" the error and self-correct.
4.  **Isolation**: Each skill should be a self-contained CLI tool, runnable by humans and agents alike.

## Technical Deep Dive (Perplexity)

### 1. Architecture: The "Executable Spec" Pattern

The most robust pattern for Agent tools is treating them as "Executable Specifications". The tool isn't just a script; it's a strongly-typed service that exposes its own API definition.

- **CLI as API**: The Command Line Interface is the API. Arguments should be POSIX-compliant.
- **Schema First**: By defining inputs as Pydantic models, we can auto-generate the OpenAI function calling schema directly from the tool info, keeping the Agent's prompt in sync with the actual code.

### 2. The Golden Stack: Typer + Pydantic

- **Typer**: leveraged for its ability to generate help docs and handle CLI parsing using Python type hints. It supports subcommands, autocompletion, and rich output.
- **Pydantic**: Used for validation. Agent inputs (LLM outputs) are often "dirty" or malformed. Pydantic ensures that the script only executes if the data is valid, or returns a helpful validation error.

### 3. Error Handling for Agents

Agents are "non-deterministic users". They make mistakes. A good tool helps the user fix the mistake.

- **Bad**: `KeyError: 'foo'` (Agent is confused).
- **Good**: `{"status": "error", "code": "missing_param", "message": "The parameter 'foo' is required."}` (Agent can read this and retry with the parameter).

## API & Implementation Reference (Context7 & Patterns)

### Standard Skill Template

The following pattern demonstrates a self-documenting, strongly-typed skill.

```python
import sys
import json
from typing import Optional
import typer
from pydantic import BaseModel, Field

# 1. Define Input Schema
class InputModel(BaseModel):
    query: str = Field(..., description="The search query or main input")
    limit: int = Field(5, ge=1, le=100, description="Max results to return")
    verbose: bool = Field(False, description="Enable detailed logging")

# 2. Define Output Schema
class OutputModel(BaseModel):
    status: str
    data: Optional[dict] = None
    error: Optional[str] = None

app = typer.Typer()

@app.command()
def main(
    query: str = typer.Option(..., help="Main input query"),
    limit: int = typer.Option(5, help="Max results"),
    verbose: bool = typer.Option(False, help="Debug mode"),
    schema: bool = typer.Option(False, help="Print input JSON schema and exit")
):
    """
    My Powerful Skill: Does X, Y, and Z.
    """
    # 3. Schema Discovery
    if schema:
        print(InputModel.model_json_schema_json(indent=2))
        return

    # 4. Validation (Construct Model)
    try:
        inputs = InputModel(query=query, limit=limit, verbose=verbose)
    except Exception as e:
        # Structured Error for Agent
        print(json.dumps(OutputModel(status="error", error=str(e)).model_dump()))
        sys.exit(1)

    # 5. Business Logic
    try:
        # ... logic here ...
        result = {"foo": "bar", "input": inputs.query}

        # 6. Structured Success Response
        print(json.dumps(OutputModel(status="success", data=result).model_dump()))

    except Exception as e:
        print(json.dumps(OutputModel(status="error", error=str(e)).model_dump()))
        sys.exit(1)

if __name__ == "__main__":
    app()
```

## Action Plan

- [ ] **Scaffold**: Update `skill_factory.py` to generate this new template instead of the old argparse one.
- [ ] **Dependencies**: Ensure `typer` and `pydantic` are installed in the global environment (or managed via the skill's venv).
- [ ] **Registry**: Implement a mechanism to scan `skills/*/SKILL.md` or run `--schema` to build a dynamic tool catalog for the main Agent.
