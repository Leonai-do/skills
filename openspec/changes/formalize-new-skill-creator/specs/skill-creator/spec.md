# Skill Creator Capability

## ADDED Requirements

### Requirement: Architecture - Meta-Agent Role

The Skill Creator Agent MUST operate as an "Architect" distinct from a user, using a specific generation loop to ensure quality and separation of concerns.

#### Scenario: Prompting

- **Step:** The system instantiates the Skill Creator Agent.
- **Step:** The system injects the "Architect" persona into the system prompt.
- **Verify:** Agent distinguishes between its own instruction context and the generated content.
- **Verify:** Agent executes the "Generate -> Critique -> Revise" loop.

### Requirement: Core Structure - The Golden Rule

Standardization is critical. Agents MUST use the provided tooling to generate the directory structure rather than inventing it.

#### Scenario: Initialization

- **Step:** Agent starts a new skill task.
- **Step:** Agent runs `python scripts/init_skill.py <skill-name>` immediately.
- **Verify:** Directory structure matches the canonical template.
- **Verify:** Directory name uses hyphen-case.

### Requirement: Content - Strict File Sandbox

Skills MUST be lean and devoid of auxiliary metadata files that clutter the context window.

#### Scenario: File Creation

- **Step:** Agent creates or modifies files in the skill directory.
- **Verify:** NO `README.md`, `INSTALL.md`, `CHANGELOG.md`, `LICENSE`, or `.gitignore` files exist.
- **Verify:** All executable logic is in `scripts/`.
- **Verify:** All documentation is in `references/` or `SKILL.md`.

### Requirement: Content - Conciseness

Skill documentation MUST remain small to preserve the context window for the user's task.

#### Scenario: Refactoring Large Files

- **Step:** Agent identifies `SKILL.md` > 500 lines.
- **Step:** Agent extracts content to `references/`.
- **Verify:** `SKILL.md` is under 500 lines.
- **Step:** Agent identifies reference > 1000 lines.
- **Verify:** File is summarized or structured for grep search.

### Requirement: Validation - Definition of Done

The agent MUST self-validate its output to ensure functionality and completeness.

#### Scenario: Completion Check

- **Step:** Agent attempts to mark task as complete.
- **Verify:** NO `TODO`, `[INSERT]`, or placeholder strings exist in any file.
- **Verify:** `python scripts/package_skill.py <skill-name>` exits with success code 0.
