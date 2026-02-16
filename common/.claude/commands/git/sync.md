---
argument-hint: [--all-changes | --session (default)] [--all-repos | --repo (default)]
---
Git sync command. Args: $ARGUMENTS

Parse the arguments to determine behavior along two axes:

**Changes scope:**
- `--all-changes` → commit everything dirty, including pre-existing uncommitted changes
- `--session` (default) → commit only changes made in this session, ignore pre-existing

**Repo scope:**
- `--all-repos` → operate on all project repos (working directory + additional working directories configured for this session — not unrelated repos elsewhere on disk)
- `--repo` (default) → operate on the current working directory's repo only

If no arguments are provided, default to `--session --repo`.

Then proceed:
- Group changes into logical commits by feature/fix/purpose
- Run `bd sync` before and after commits if beads exists
- Push all changes to remote
- Verify repo(s) show clean status (for --all-changes mode)
