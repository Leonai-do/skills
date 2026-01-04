# Skill Creator Spec

## Purpose

The Skill Creator specification defines the standard tooling and structure for creating new agent skills in the Agent-Skills repository. It ensures all skills follow a consistent, validated structure that enables reliable discovery and execution by AI agents.

## Requirements

### Requirement: Skill Creation

The system MUST provide an automated way to generate new skill scaffolds to ensure consistency.

#### Scenario: Creating a New Skill

- **Given** the user wants to add a new capability to the agent
- **Then** the agent MUST use the Skill Creator standard
- **And** the agent MUST scaffold the skill using `skill_factory.py`
- **And** the skill MUST reside in `skills/{name}/`
- **And** the skill MUST have a `SKILL.md` file

### Requirement: Skill Structure

All skills MUST adhere to a strict directory and file structure to be recognized by the agent.

#### Scenario: Skill Structure

- **Given** a new skill is created
- **Then** it MUST follow the defined folder structure (`SKILL.md`, `scripts/`, `assets/`, `references/`)
- **And** python scripts MUST use PEP 723 metadata for dependencies

### Requirement: Documentation

The Skill Creator system MUST be fully documented to guide future skill development.

#### Scenario: Documentation

- **Given** the Skill Creator system
- **Then** it MUST provide comprehensive documentation in `docs/skills/`
