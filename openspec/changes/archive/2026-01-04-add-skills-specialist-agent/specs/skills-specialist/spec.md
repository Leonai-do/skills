## ADDED Requirements

### Requirement: Skillz Execution with Fallback

The `skills-specialist` agent SHALL execute requested skills using the `skillz` MCP server primarily, and MUST transparently fall back to reading skill definitions from the local file system if the MCP server is unavailable or returns an error.

#### Scenario: Primary MCP Execution

- **WHEN** the user requests a task handled by a skill (e.g., "create a PDF")
- **AND** the `skillz` MCP server is active
- **THEN** the agent invokes the corresponding MCP tool
- **AND** returns the result to the user.

#### Scenario: Fallback File System Execution

- **WHEN** the user requests a task handled by a skill
- **AND** the `skillz` MCP tool fails or is unreachable
- **THEN** the agent reads the `SKILL.md` from `/mnt/d/LeonAI_DO/dev/Agent-Skills/skills-repository/<skill-name>/`
- **AND** follows the instructions in the markdown file to execute the task manually (e.g. running scripts via terminal).

### Requirement: Protocol Compliance

The `skills-specialist` agent SHALL strictly adhere to the input/output schemas defined in each skill's `SKILL.md`, regardless of execution method (MCP or Fallback).

#### Scenario: Schema Validation

- **WHEN** executing a skill
- **THEN** the agent verifies that provided inputs match the `Reference Patterns` or schema defined in the skill's documentation.
