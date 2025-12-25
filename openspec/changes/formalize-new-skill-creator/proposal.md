# Proposal: Transform Skill Creator into an Autonomous Agent

## Why

The current `skills/skill-creator` is a passive guide. To scale skill creation, we need an autonomous "Skill Creator Agent" that can reliably build high-quality skills with minimal human oversight. We will transform the existing `skill-creator` skill into this Agent by upgrading its instructions to a rigorous System Prompt and enforcing strict validation rules.

## What Changes

### Transformation

- **Upgrade `skills/skill-creator`**: Rewrite `SKILL.md` to be an "Agent Architecture" prompt (Role: Architect, Loop: Generate/Critique/Revise).
- **Enforce Rules**: Hardcode the "No Auxiliaries", "Progressive Disclosure", and "Definition of Done" rules into the Agent's core instructions.

### OpenSpec Formalization

- **Define Capability**: Establish `skill-creator` as a formal OpenSpec capability in `openspec/specs/skill-creator/spec.md`.
- **Requirements**: The spec now explicitly requires the Agent to function as an "Architect" and self-validate using `package_skill.py`.

### New Capabilities

- `skill-creator` (Now an Autonomous Agent)
- (Plus previously integrated skills: `algorithmic-art`, `brand-guidelines`, etc.)

### New Spec: Skill Creator Rules

Strict rules for skill creation have been formally defined in `specs/skill-creator/spec.md`, enforcing:

- Mandatory use of `init_skill.py`.
- Strict file sandbox (no READMEs).
- Definition of Done (No TODOs).
- Self-validation via `package_skill.py`.
