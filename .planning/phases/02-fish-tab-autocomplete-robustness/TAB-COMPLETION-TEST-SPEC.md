# Tab Completion System - Test Specification

This document defines expected behavior for Tab, Ctrl+Tab, and Ctrl+Backspace across all contexts.

## Test Notation

- `|` = cursor position
- `+Tab` = press Tab key
- `+Ctrl+Tab` = press Ctrl+Tab
- `+Ctrl+Backspace` = press Ctrl+Backspace
- Grey text = autosuggestion from history
- `→` = expected result

---

## 1. Tab Completion - Path Contexts

### 1.1 Empty/Partial Directory Argument

**Scenario:** `cd |` (cursor after space, no input)
- **+Tab** → fzf opens with:
  - Immediate children of CWD labeled `[child]` (first priority)
  - Zoxide frecent dirs labeled `[z:N]` where N is rank
  - fre frecent dirs labeled `[fre:N]`
  - Deep filesystem dirs labeled `[fs]`

**Scenario:** `cd ~/.config/cjar/|` (full path to existing dir)
- **+Tab** → fzf opens with:
  - Immediate children of `~/.config/cjar/` labeled `[child]`
  - No frecency results (not CWD-relative)
  - Deep dirs under `~/.config/cjar/` labeled `[fs]`

**Scenario:** `cd ~/Do|` (partial path)
- **+Tab** → fzf opens with:
  - Matches starting with `~/Do*`
  - Query pre-filled with "Do"
  - Immediate children of `~/ ` labeled `[child]`
  - Frecency matches labeled `[z:N]` or `[fre:N]`

### 1.2 File Arguments

**Scenario:** `nvim |` (cursor after space, no input)
- **+Tab** → fzf opens with:
  - Recently edited files labeled `[fre:1]`, `[fre:2]` etc (first priority)
  - Local files in CWD labeled `[local]`
  - Deep filesystem files labeled `[fs]`

**Scenario:** `nvim ~/.config/|` (partial path to dir)
- **+Tab** → fzf opens with:
  - Files under `~/.config/` labeled `[local]` if depth 1
  - Files under `~/.config/` labeled `[fs]` if deeper
  - No frecency (not CWD-relative)

---

## 2. Ctrl+Tab - Segment Accept from Autosuggestion

**Goal:** Accept next segment of autosuggestion INCLUDING delimiter.
**Delimiters:** `/` (paths), space (args), `--` (flags), `=` (assignments), `:` (key-value), opening quote

### 2.1 Path Segments

**Scenario:** Autosuggestion = `cd /home/rash/Documents/work`

| Cursor Start | Ctrl+Tab Press | Cursor After | Notes |
|--------------|----------------|--------------|-------|
| `cd\|` | 1st | `cd /\|` | Space + first `/` accepted |
| `cd /\|` | 2nd | `cd /home/\|` | Up to and including next `/` |
| `cd /home/\|` | 3rd | `cd /home/rash/\|` | Up to and including next `/` |
| `cd /home/rash/\|` | 4th | `cd /home/rash/Documents/\|` | Up to and including next `/` |
| `cd /home/rash/Documents/\|` | 5th | `cd /home/rash/Documents/work\|` | Last segment, no trailing `/` |

**Scenario:** Autosuggestion = `cd "/home/rash/some dir/subdir"`

| Cursor Start | Ctrl+Tab Press | Cursor After | Notes |
|--------------|----------------|--------------|-------|
| `cd\|` | 1st | `cd "\|` | Space + opening quote (quote is delimiter) |
| `cd "\|` | 2nd | `cd "/home/\|` | Inside quotes: `/` is delimiter, space is NOT |
| `cd "/home/\|` | 3rd | `cd "/home/rash/\|` | `/` delimiter |
| `cd "/home/rash/\|` | 4th | `cd "/home/rash/some dir/\|` | Space NOT delimiter in quotes |
| `cd "/home/rash/some dir/\|` | 5th | `cd "/home/rash/some dir/subdir/\|` | Trailing `/` included at end |

### 2.2 Flag/Argument Segments

**Scenario:** Autosuggestion = `claude --allow-dangerously-skip-permissions`

| Cursor Start | Ctrl+Tab Press | Cursor After | Notes |
|--------------|----------------|--------------|-------|
| `claude\|` | 1st | `claude \|` | Space is delimiter |
| `claude \|` | 2nd | `claude --\|` | `--` is delimiter (flag start) |
| `claude --\|` | 3rd | `claude --allow-dangerously-skip-permissions\|` | No more delimiters, accept rest |

**Alternative if middle of word:**
| Cursor Start | Ctrl+Tab Press | Cursor After | Notes |
|--------------|----------------|--------------|-------|
| `clau\|de` | 1st | `claude \|` | Complete to next delimiter (space) |

**Scenario:** Autosuggestion = `git commit -m "fix: bug"`

| Cursor Start | Ctrl+Tab Press | Cursor After | Notes |
|--------------|----------------|--------------|-------|
| `git\|` | 1st | `git \|` | Space delimiter |
| `git \|` | 2nd | `git commit \|` | Space delimiter |
| `git commit \|` | 3rd | `git commit -m \|` | Space delimiter |
| `git commit -m \|` | 4th | `git commit -m "\|` | Opening quote delimiter |
| `git commit -m "\|` | 5th | `git commit -m "fix: bug"\|` | No more delimiters in quote context |

### 2.3 Remote Paths

**Scenario:** Autosuggestion = `scp server:/home/user/file.txt .`

| Cursor Start | Ctrl+Tab Press | Cursor After | Notes |
|--------------|----------------|--------------|-------|
| `scp\|` | 1st | `scp \|` | Space delimiter |
| `scp \|` | 2nd | `scp server:\|` | `:` is delimiter (host separator) |
| `scp server:\|` | 3rd | `scp server:/home/\|` | `/` delimiter (in path context after `:`) |
| `scp server:/home/\|` | 4th | `scp server:/home/user/\|` | `/` delimiter |
| `scp server:/home/user/\|` | 5th | `scp server:/home/user/file.txt \|` | Space delimiter |

### 2.4 Delimiter Runs (multiple consecutive delimiters)

**Scenario:** Autosuggestion = `rsync -av -- /source/ /dest/`

| Cursor Start | Ctrl+Tab Press | Cursor After | Notes |
|--------------|----------------|--------------|-------|
| `rsync\|` | 1st | `rsync \|` | Space |
| `rsync \|` | 2nd | `rsync -av \|` | Space (treat `-av` as one arg) |
| `rsync -av \|` | 3rd | `rsync -av -- \|` | `-- ` treated as single delimiter run |
| `rsync -av -- \|` | 4th | `rsync -av -- /source/\|` | `/` delimiter (trailing slash included) |
| `rsync -av -- /source/\|` | 5th | `rsync -av -- /source/ \|` | Space delimiter |

### 2.5 No Autosuggestion

**Scenario:** `cd |` (no grey suggestion)
- **+Ctrl+Tab** → Falls back to Tab behavior (opens fzf with smart completion)

---

## 3. Ctrl+Backspace - Segment Delete (Inverse of Ctrl+Tab)

**Goal:** Delete previous segment EXCLUDING delimiter.
**Same delimiter rules as Ctrl+Tab, but exclude delimiter.**

### 3.1 Path Segments

**Scenario:** Current command = `cd /home/rash/Documents/work|`

| Cursor Start | Ctrl+Backspace Press | Cursor After | Notes |
|--------------|----------------------|--------------|-------|
| `cd /home/rash/Documents/work\|` | 1st | `cd /home/rash/Documents/\|` | Delete `work`, keep `/` |
| `cd /home/rash/Documents/\|` | 2nd | `cd /home/rash/\|` | Delete `Documents`, keep `/` |
| `cd /home/rash/\|` | 3rd | `cd /home/\|` | Delete `rash`, keep `/` |
| `cd /home/\|` | 4th | `cd /\|` | Delete `home`, keep `/` |
| `cd /\|` | 5th | `cd \|` | Delete `/`, keep space |
| `cd \|` | 6th | `\|` | Delete `cd`, keep nothing |

**Scenario:** Current command = `cd "/home/rash/some dir/subdir"|`

| Cursor Start | Ctrl+Backspace Press | Cursor After | Notes |
|--------------|----------------------|--------------|-------|
| `cd "/home/rash/some dir/subdir"\|` | 1st | `cd "/home/rash/some dir/\|` | Delete `subdir"`, keep `/` |
| `cd "/home/rash/some dir/\|` | 2nd | `cd "/home/rash/\|` | Delete `some dir` (space NOT delimiter in quotes), keep `/` |
| `cd "/home/rash/\|` | 3rd | `cd "/home/\|` | Delete `rash`, keep `/` |
| `cd "/home/\|` | 4th | `cd "/\|` | Delete `home`, keep `/` |
| `cd "/\|` | 5th | `cd \|` | Delete `"`, keep space |

### 3.2 Flag/Argument Segments

**Scenario:** Current command = `claude --allow-dangerously-skip-permissions|`

| Cursor Start | Ctrl+Backspace Press | Cursor After | Notes |
|--------------|----------------------|--------------|-------|
| `claude --allow-dangerously-skip-permissions\|` | 1st | `claude --\|` | Delete entire flag arg (no internal delimiters), keep `--` |
| `claude --\|` | 2nd | `claude \|` | Delete `--`, keep space |
| `claude \|` | 3rd | `\|` | Delete `claude`, keep nothing |

**Scenario:** Current command = `git commit -m "fix: bug"|`

| Cursor Start | Ctrl+Backspace Press | Cursor After | Notes |
|--------------|----------------------|--------------|-------|
| `git commit -m "fix: bug"\|` | 1st | `git commit -m "\|` | Delete `fix: bug"`, keep `"` |
| `git commit -m "\|` | 2nd | `git commit -m \|` | Delete `"`, keep space |
| `git commit -m \|` | 3rd | `git commit \|` | Delete `-m`, keep space |
| `git commit \|` | 4th | `git \|` | Delete `commit`, keep space |
| `git \|` | 5th | `\|` | Delete `git`, keep nothing |

### 3.3 Behavior at Delimiter Boundaries

**CRITICAL:** Ctrl+Backspace should delete the segment BEFORE the cursor, not including the delimiter immediately before the cursor.

**Example:** Current = `cd /home/|rash/Documents`
- **+Ctrl+Backspace** → `cd /|rash/Documents` (delete `home`, keep `/` before cursor)

**Example:** Current = `git commit -m |"message"`
- **+Ctrl+Backspace** → `git commit |"message"` (delete `-m`, keep space before cursor)

---

## 4. Ctrl+Shift+Backspace - Full Argument Delete

**Goal:** Delete entire previous shell argument/token as a single unit.
**Uses fish shell tokenization, not delimiter parsing.**

### 4.1 Simple Arguments

**Scenario:** Current command = `git commit -m "fix bug" --amend|`

| Cursor Start | Ctrl+Shift+Backspace | Cursor After | Notes |
|--------------|----------------------|--------------|-------|
| `git commit -m "fix bug" --amend\|` | 1st | `git commit -m "fix bug" \|` | Delete `--amend` token |
| `git commit -m "fix bug" \|` | 2nd | `git commit -m \|` | Delete `"fix bug"` token (quoted = one token) |
| `git commit -m \|` | 3rd | `git commit \|` | Delete `-m` token |
| `git commit \|` | 4th | `git \|` | Delete `commit` token |
| `git \|` | 5th | `\|` | Delete `git` token |

### 4.2 Quoted Paths

**Scenario:** Current command = `cd "/home/rash/some dir/subdir"|`

| Cursor Start | Ctrl+Shift+Backspace | Cursor After | Notes |
|--------------|----------------------|--------------|-------|
| `cd "/home/rash/some dir/subdir"\|` | 1st | `cd \|` | Delete entire quoted path (one token) |
| `cd \|` | 2nd | `\|` | Delete `cd` |

### 4.3 Remote Commands

**Scenario:** Current command = `scp server:/home/user/file.txt /local/dest/|`

| Cursor Start | Ctrl+Shift+Backspace | Cursor After | Notes |
|--------------|----------------------|--------------|-------|
| `scp server:/home/user/file.txt /local/dest/\|` | 1st | `scp server:/home/user/file.txt \|` | Delete `/local/dest/` token |
| `scp server:/home/user/file.txt \|` | 2nd | `scp \|` | Delete `server:/home/user/file.txt` token |
| `scp \|` | 3rd | `\|` | Delete `scp` |

---

## 5. Multiline Commands

For all three keybindings, when in multiline context:
- **Tab:** Normal smart completion
- **Ctrl+Tab:** Accept entire current line (simplified, not segment-by-segment)
- **Ctrl+Backspace:** Delete entire current line
- **Ctrl+Shift+Backspace:** Delete entire current line (same as Ctrl+Backspace)

---

## 6. Edge Cases

### 6.1 URLs

**Scenario:** Autosuggestion = `curl https://api.example.com/v1/users/123`

**Ctrl+Tab progression:**
| Start | After Ctrl+Tab | Notes |
|-------|----------------|-------|
| `curl\|` | `curl \|` | Space delimiter |
| `curl \|` | `curl https:\|` | `:` delimiter |
| `curl https:\|` | `curl https://api.example.com/v1/\|` | `/` delimiters |
| Continue... | ... | `/` between path segments |

### 6.2 Escaped Characters

**Scenario:** Autosuggestion = `cd /path/with\\ space/dir`

**Ctrl+Tab should treat `\\ ` (escaped space) as NOT a delimiter:**
| Start | After Ctrl+Tab | Notes |
|-------|----------------|-------|
| `cd\|` | `cd \|` | Space delimiter |
| `cd \|` | `cd /path/\|` | `/` delimiter |
| `cd /path/\|` | `cd /path/with\\ space/\|` | `\\ ` is NOT delimiter, `/` is |

### 6.3 Empty Segments

**Scenario:** Autosuggestion = `cd //double//slash//path`

**Ctrl+Tab should accept delimiter runs as units:**
| Start | After Ctrl+Tab | Notes |
|-------|----------------|-------|
| `cd\|` | `cd \|` | Space |
| `cd \|` | `cd //\|` | `//` treated as one delimiter unit |
| `cd //\|` | `cd //double//\|` | `//` treated as one delimiter unit |

---

## Summary of Delimiter Rules

### Tab Completion
- Triggers on: Space after command, partial path, trigger words
- Does NOT trigger on: Full directory path (delegates to fish native)

### Ctrl+Tab (Accept Segment, INCLUDE delimiter)
**Context-aware delimiters:**
- Outside quotes: `/`, space, `--`, `=`, `:`, opening quote
- Inside quotes: `/` only (spaces are literal)
- Delimiter runs (`//`, `-- `, etc.): Treated as single unit
- Escaped chars (`\\ `, `\"`): NOT delimiters

### Ctrl+Backspace (Delete Segment, EXCLUDE delimiter)
- Same delimiter rules as Ctrl+Tab
- Deletes segment BEFORE cursor
- Keeps delimiter immediately before cursor

### Ctrl+Shift+Backspace (Delete Full Argument)
- Uses fish shell tokenization
- One argument = one deletion (respects quotes and escaping)
- Simpler than Ctrl+Backspace: whole token at once
