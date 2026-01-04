# Skill Creator Spec Delta

## ADDED Requirements

### Requirement: Skill Constraints

The system MUST enforce strict negative constraints to maintain agentic purity.

#### Scenario: Banned Files

- **Given** a skill directory
- **Then** it MUST NOT contain `requirements.txt`
- **And** it MUST NOT contain `README.md`
- **And** it MUST NOT contain `__init__.py`
- **And** it MUST NOT contain `.gitignore`
- **And** it MUST NOT contain `LICENSE`

## MODIFIED Requirements

### Requirement: Skill Structure

All skills MUST adhere to a strict directory and file structure to be recognized by the agent.

#### Scenario: Scripts Location

- **Given** executable logic for a skill
- **Then** it MUST be located in the `scripts/` subdirectory
- **And** it MUST NOT be in the root skill directory

#### Scenario: PEP 723 Metadata

- **Given** a python script in `scripts/`
- **Then** it MUST use PEP 723 (`# /// script`) to define dependencies
- **And** it MUST NOT rely on external `requirements.txt`
