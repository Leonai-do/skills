## Context

The `skillz` MCP server provides a standardized interface for agents to use tools. However, reliance on a single server introduces a point of failure. We need an agent that can gracefully degrade to direct file access if the server is down.

## Goals / Non-Goals

- **Goal**: Create an agent that executes skills reliably.
- **Goal**: Implement a transparent fallback mechanism.
- **Non-Goal**: Re-implement the functionality of _every_ skill. The agent reads instructions, it doesn't hardcode them.

## Decisions

- **Decision**: The agent will reside in `global_workflows` to be accessible system-wide in Antigravity.
- **Decision**: Fallback path is hardcoded to `/mnt/d/LeonAI_DO/dev/Agent-Skills/skills-repository`.
- **Decision**: The agent acts as a proxy; it does not replace the individual skills but "orchestrates" them.

## Risks / Trade-offs

- **Risk**: Direct file reading might be slower or more token-intensive than MCP calls.
  - **Mitigation**: Use this only as a fallback.
- **Risk**: Skills might depend on `scripts/` that require a specific runtime (Python env) which the MCP handles but the agent might not.
  - **Mitigation**: The agent will be instructed to use `run_command` with the correct virtual environment if manual execution is needed.

## Open Questions

- None at this stage.
