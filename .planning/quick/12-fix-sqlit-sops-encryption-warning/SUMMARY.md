# Quick Task 12: Fix sqlit SOPS encryption warning

## Problem

The `sqlit` wrapper was showing this warning on every run:
```
⚠️  Warning: /Users/rash/.sqlit/connections.json is not SOPS-encrypted!
```

## Root Cause

Two issues:
1. The connections.json file was committed unencrypted in commit `beb62d0` (should have been SOPS-encrypted)
2. The wrapper detected unencrypted file but only warned - never auto-encrypted it

## Solution

1. **Modified wrapper** (`workmbp/local/bin/sqlit`) to auto-encrypt unencrypted files on first detection
   - Commit: b0d6c0e
   - Instead of just warning, now encrypts the file automatically
   - Then proceeds with normal decrypt → run → re-encrypt flow

2. **Re-encrypted the file in repo** (`workmbp/config/.sqlit/connections.json`)
   - Commit: 9030647
   - File was in unencrypted state in git
   - Re-encrypted with SOPS using AGE key

## Result

- No more warnings on sqlit runs
- File properly encrypted in repo and at runtime
- Wrapper now handles both scenarios: encrypted (normal) and unencrypted (auto-fix)
