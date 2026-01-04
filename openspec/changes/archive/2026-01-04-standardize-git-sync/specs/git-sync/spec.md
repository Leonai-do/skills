# Git Sync Capability

## ADDED Requirements

### Requirement: [CAP-SYNC-001] Automated Change Detection

The system MUST be able to detect all pending changes in the current git repository, including staged, unstaged, and untracked files.

#### Scenario: Dirty Working Directory

Given a repo with modified `foo.py` and new `bar.py`
When `git-sync` is triggered
Then it identifies `foo.py` as modified and `bar.py` as new.

### Requirement: [CAP-SYNC-002] Content-Aware Commit Generation

The system MUST generate a commit message that accurately reflects the detected changes.

#### Scenario: Generate Message

Given a diff showing a bug fix in `login.py`
When `git-sync` analyzes the diff
Then it produces a commit message like "Fix login bug in login.py".

### Requirement: [CAP-SYNC-003] Atomic Sync Operation

The system MUST perform the add, commit, and push operations as a single logical unit.

#### Scenario: Successful Sync

Given pending changes
When `git-sync` completes successfully
Then the working directory is clean AND the changes are pushed to the remote branch.
