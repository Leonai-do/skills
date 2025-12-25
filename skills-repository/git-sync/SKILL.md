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

- Detects pending changes (staged and unstaged)
- Generates a descriptive commit message (heuristic-based)
- stages all changes (`git add .`)
- Commits with the generated message
- Pushes to the current branch

## Requirements

- Git installed and configured
- Current directory must be a git repository
