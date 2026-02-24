# Beads Setup Guide

This guide documents how to replicate the beads issue tracker setup on a new machine.
The dotfiles repo is at `~/.dotfiles` (`git@github.com:robertoash/.dotfiles.git`).
This is a fish shell environment on Linux.

## What beads is

`bd` is a CLI-based git-backed issue tracker. Issues live in `.beads/` alongside
the code and sync via a dedicated `beads-sync` git branch. The binary is at
`~/.local/bin/bd`.

## Step 1: Install the bd binary

```bash
go install github.com/steveyegge/beads/cmd/bd@latest
```

Verify: `bd --version`

## Step 2: Register the custom git merge driver

Must be added to the repo's local git config (NOT global) so JSONL merges are
handled by bd instead of git's default text merge:

```bash
cd ~/.dotfiles
git config merge.beads.driver "bd merge %A %O %A %B"
git config merge.beads.name "bd JSONL merge driver"
git config extensions.worktreeconfig true
```

Verify the `.gitattributes` already has (it's committed to the repo):

```
.beads/issues.jsonl merge=beads
```

## Step 3: Set up the beads-sync worktree

This is the critical manual step. The `beads-sync` branch already exists on the
remote. You need a sparse git worktree that checks out ONLY the `.beads/` directory
from that branch, placed inside `.git/beads-worktrees/beads-sync/`.

Run these commands from `~/.dotfiles`:

```bash
# Create the directory and add the worktree
mkdir -p .git/beads-worktrees
git worktree add .git/beads-worktrees/beads-sync beads-sync

# Write sparse checkout config directly to the worktree-local config file.
# Do NOT use `git -C <worktree> config` — that writes to the main .git/config
# instead of .git/worktrees/beads-sync/config.worktree, polluting the main repo.
printf '[core]\n\tsparseCheckout = true\n\tsparseCheckoutCone = false\n' \
    > .git/worktrees/beads-sync/config.worktree

# Write the sparse checkout pattern
mkdir -p .git/worktrees/beads-sync/info
echo "/.beads/" > .git/worktrees/beads-sync/info/sparse-checkout

# Apply sparse checkout (removes all files except .beads/ from the worktree)
git -C .git/beads-worktrees/beads-sync checkout
```

Verify the worktree only contains `.beads/` and `.git`:

```bash
ls .git/beads-worktrees/beads-sync/
# Expected: .beads  .git
```

Verify git worktree list:

```bash
git worktree list
# Expected:
# ~/.dotfiles                                 [main]
# ~/.dotfiles/.git/beads-worktrees/beads-sync [beads-sync]
```

> **Key detail:** `core.sparseCheckout` must be set in the worktree-local config
> (`.git/worktrees/beads-sync/config.worktree`), NOT the main `.git/config`. The
> sparse-checkout pattern file goes to `.git/worktrees/beads-sync/info/sparse-checkout`.

## Step 4: Install git hooks in the dotfiles repo

```bash
cd ~/.dotfiles
bd hooks install
```

This installs pre-commit, post-checkout, post-merge, prepare-commit-msg, and
pre-push hooks that delegate to bd for JSONL sync.

## Step 5: Configure Claude Code global hooks

```bash
bd setup claude
```

This installs beads hooks into `~/.claude/settings.json` so Claude Code sessions
get the beads workflow context on startup.

## Step 6: Verify the sync-branch config

The file `~/.dotfiles/.beads/config.yaml` is committed and already contains:

```yaml
sync-branch: "beads-sync"
```

This tells bd to use the beads-sync branch/worktree for sync. No changes needed —
just verify it exists.

## Step 7: Sync to pull current issues

```bash
cd ~/.dotfiles
bd sync
```

This imports the latest `issues.jsonl` from the beads-sync branch into the local
SQLite database.

## Step 8: Run setup.py

```bash
cd ~/.dotfiles
python setup.py
```

This runs `beads_setup.py` which re-runs `bd setup claude` and `bd hooks install`
as part of the standard dotfiles setup, ensuring everything stays consistent.

## Verification checklist

```bash
bd --version               # bd binary works
bd list                    # issues load from database
bd sync                    # no errors
git worktree list          # shows both main and beads-sync worktrees
git -C ~/.dotfiles config merge.beads.driver  # outputs: bd merge %A %O %A %B
```

## Files involved

| Path | Purpose |
|------|---------|
| `~/.local/bin/bd` | The beads CLI binary |
| `~/.dotfiles/.beads/` | Issue database, JSONL export, config |
| `~/.dotfiles/.beads/config.yaml` | Sets `sync-branch: "beads-sync"` |
| `~/.dotfiles/.git/config` | Merge driver + `extensions.worktreeconfig` |
| `~/.dotfiles/.git/beads-worktrees/beads-sync/` | Sparse worktree on beads-sync branch |
| `~/.dotfiles/.git/hooks/` | Git hooks delegating to bd |
| `~/.claude/settings.json` | Global Claude Code hooks for beads workflow context |
