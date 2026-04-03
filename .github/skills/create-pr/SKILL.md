---
name: create-pr
description: Creates a Pull Request from the current branch after pushing it to the remote repository.
---

# Instructions

Use this skill when you have committed your changes and want to push the current branch to the remote repository and open a Pull Request.
This skill will execute the `run.sh` script which pushes the branch and uses the `gh` CLI to create a PR with predefined title and body.

## Execution
Execute the script located at `run.sh` in this folder.
Ensure you are authenticated with GitHub CLI (`gh auth status`) before running.
