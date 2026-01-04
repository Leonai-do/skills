---
name: git-sync
description: Automates the process of staging, committing, and pushing changes to the current git branch.
version: 1.0.0
usage: |
  python git_sync.py
---

# Git Sync Skill

This skill allows you to synchronize your current local changes with the remote repository in a single step.

## Features

- **Detects Pending Changes**: Identifies staged, unstaged, and untracked files.
- **Auto-Commit Message**: Generates a concise, descriptive commit message based on the file changes (e.g., "Update main.py; Add utils.py").
- **One-Step Sync**: Stages all changes (`git add .`), commits, and pushes to the current branch.
- **Smart Push**: Automatically handles upstream setup if waiting.

## Requirements

- Git installed and configured.
- Current directory must be a git repository.

## Usage

Simply run the script from the root of your git repository (or anywhere inside it):

```bash
python3 /path/to/git_sync.py
```

## Instructions

1. **Load Skill**: When you need to save your work.
2. **Execute**: Run the `git_sync.py` script.
3. **Verify**: Check the output to confirm the commit message and push status.
