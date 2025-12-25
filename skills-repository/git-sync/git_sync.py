import os
import subprocess
import sys
import json
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(e.stderr)
        raise

def get_git_status():
    """Get the status of the current git repository."""
    status_output = run_command("git status --porcelain")
    return status_output

def generate_commit_message(status_output):
    """
    Generate a commit message based on the status.
    In a real scenario, this could use an LLM. For now, we use a heuristic.
    """
    if not status_output:
        return None

    lines = status_output.split('\n')
    modified = [l for l in lines if l.startswith(' M') or l.startswith('M ')]
    added = [l for l in lines if l.startswith('??') or l.startswith('A ')]
    deleted = [l for l in lines if l.startswith(' D') or l.startswith('D ')]

    parts = []
    if modified:
        parts.append(f"Modify {len(modified)} files")
    if added:
        parts.append(f"Add {len(added)} files")
    if deleted:
        parts.append(f"Delete {len(deleted)} files")

    if not parts:
        return "Update repository"
    
    return ", ".join(parts)

def main():
    try:
        # Check if we are in a git repo
        run_command("git rev-parse --is-inside-work-tree")
    except:
        print("Error: Not a git repository.")
        sys.exit(1)

    status = get_git_status()
    if not status:
        print("No changes to sync.")
        sys.exit(0)

    print("Detected changes:")
    print(status)

    message = generate_commit_message(status)
    print(f"\nGeneratred commit message: {message}")

    # Add all changes
    print("Adding changes...")
    run_command("git add .")

    # Commit
    print("Committing...")
    run_command(f'git commit -m "{message}"')

    # Push
    print("Pushing...")
    # Get current branch
    branch = run_command("git rev-parse --abbrev-ref HEAD")
    run_command(f"git push origin {branch}")

    print("Sync complete!")

if __name__ == "__main__":
    main()
