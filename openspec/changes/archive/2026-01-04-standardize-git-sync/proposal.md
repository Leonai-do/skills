# Standardize Git Sync Workflow

## Why

Currently, synchronizing changes to the repository involves manual steps: checking status, adding files, writing commits, and pushing. This is prone to friction and inconsistency. A standardized "save my work" capability will automate this, ensuring changes are captured with descriptive messages and synced regularly.

## What Changes

We will introduce a new skill/script `git-sync` (or `save-work`) that:

1.  **Reads Pending Changes**: Detects modified, added, and deleted files.
2.  **Generates Commit Message**: Uses an LLM or heuristic to generate a concise, descriptive commit message based on the diff.
3.  **Englobes Everything**: Adds all changes (`git add .`) and commits them.
4.  **Updates Git**: Pushes the commit to the current branch.

### Scope

- **Target**: `skills/git-sync` (new skill)
- **Integration**: Can be called via `git-sync` or similar alias.

## Impacts

- **Workflow**: Developers/Agents can save work with a single command.
- **Quality**: Commit messages will be more consistent.
