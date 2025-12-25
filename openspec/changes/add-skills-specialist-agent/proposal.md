# Change: Add Skills Specialist Agent

## Why

We need a specialized agent capable of robustly executing tasks using the `skillz` MCP server. This agent serves as a reliability layer, ensuring that even if the MCP server is unavailable or fails, critical skills can still be accessed directly from the repository. This "hybrid" approach guarantees high availability for agent capabilities.

## What Changes

- **New Global Workflow Agent**: `skills-specialist` located in `global_workflows`.
- **Dual-Path Execution**:
  1.  **Primary**: Use `skillz` MCP server.
  2.  **Fallback**: Direct file access to `/mnt/d/LeonAI_DO/dev/Agent-Skills/skills-repository`.
- **Protocol Enforcement**: Strict adherence to the standard Agent Skills Protocol (inputs/outputs).

## Impact

- **New Capability**: `skills-specialist` added to specs.
- **New File**: `/home/lnx-leonai-do/.gemini/antigravity/global_workflows/skills-specialist.md`.
- **Dependencies**: Requires read access to the `skills-repository`.
