---
phase: quick-13
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - common/config/fish/functions/__smart_tab_complete.fish
  - common/config/fish/functions/__completion_config.fish
  - common/config/fish/functions/accept_next_path_segment.fish
  - common/config/fish/functions/custom_delete_backward_word.fish
  - common/config/fish/functions/custom_delete_backward_word_space.fish
  - common/config/fish/functions/custom_delete_forward_word.fish
  - common/config/fish/functions/custom_delete_forward_word_space.fish
autonomous: true
must_haves:
  truths:
    - "cd ~/.config/cjar/+Tab opens fzf with children of ~/.config/cjar/ instead of fish native"
    - "Ctrl+Backspace deletes the previous path segment excluding delimiter"
    - "Ctrl+Shift+Backspace deletes the previous full argument (space-delimited)"
    - "Ctrl+Tab stops at -- flag prefix when accepting autosuggestion segments"
  artifacts:
    - path: "common/config/fish/functions/custom_delete_backward_word.fish"
      provides: "Ctrl+Backspace: delete previous segment (slash-aware)"
    - path: "common/config/fish/functions/custom_delete_backward_word_space.fish"
      provides: "Ctrl+Shift+Backspace: delete previous full argument (space-only)"
    - path: "common/config/fish/functions/custom_delete_forward_word.fish"
      provides: "Ctrl+Delete: delete next segment (slash-aware)"
    - path: "common/config/fish/functions/custom_delete_forward_word_space.fish"
      provides: "Ctrl+Shift+Delete: delete next full argument (space-only)"
    - path: "common/config/fish/functions/accept_next_path_segment.fish"
      provides: "Ctrl+Tab with delimiter awareness for --, :, ="
  key_links:
    - from: "common/config/fish/conf.d/06_keybindings.fish"
      to: "custom_delete_backward_word"
      via: "bind \\e\\[127\\;5u custom_delete_backward_word"
    - from: "common/config/fish/conf.d/06_keybindings.fish"
      to: "custom_delete_backward_word_space"
      via: "bind \\e\\[127\\;6u custom_delete_backward_word_space"
---

<objective>
Fix three Tab completion system bugs from Phase 02 implementation.

Purpose: Phase 02 implemented the smart Tab completion system but left three gaps: (1) trailing-slash directory paths bypass fzf, (2) Ctrl+Backspace/Delete functions were bound but never created, (3) Ctrl+Tab only recognizes / and space as delimiters.
Output: All three bugs fixed; Tab, Ctrl+Tab, and Ctrl+Backspace work per TAB-COMPLETION-TEST-SPEC.md
</objective>

<execution_context>
@/home/rash/.claude/get-shit-done/workflows/execute-plan.md
@/home/rash/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/phases/02-fish-tab-autocomplete-robustness/TAB-COMPLETION-TEST-SPEC.md
@common/config/fish/functions/__smart_tab_complete.fish
@common/config/fish/functions/__completion_config.fish
@common/config/fish/functions/accept_next_path_segment.fish
@common/config/fish/conf.d/06_keybindings.fish
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix trailing-slash fzf bypass and create Ctrl+Backspace/Delete functions</name>
  <files>
    common/config/fish/functions/__smart_tab_complete.fish
    common/config/fish/functions/__completion_config.fish
    common/config/fish/functions/custom_delete_backward_word.fish
    common/config/fish/functions/custom_delete_backward_word_space.fish
    common/config/fish/functions/custom_delete_forward_word.fish
    common/config/fish/functions/custom_delete_forward_word_space.fish
  </files>
  <action>
**Bug 1 Fix - Trailing slash bypasses fzf:**

The issue: When the user types `cd ~/.config/cjar/` and presses Tab, the token after the trailing `/` may be empty (fish treats `/` as completing the previous token). When token is empty and `commandline -opc` gives `cd ~/.config/cjar/` as tokens, `__completion_get_type` correctly returns "dirs". BUT in `__smart_tab_complete`, the path extraction logic (lines 14-25) only fires when `string match -q -r '/' -- "$token"` succeeds. If token is empty (cursor is right after the `/`), this doesn't match, so `search_dir` stays "." and `query_part` stays empty -- meaning fzf searches CWD instead of the intended directory.

Fix in `__smart_tab_complete.fish`: After the path prefix extraction block (line 14-25), add a fallback check. If `$token` is empty, look at the PREVIOUS token from `commandline -opc`. If the previous token ends with `/` and is a valid directory path, set `search_dir` to the expanded previous token and `path_prefix` to the previous token. This way fzf will list children of the intended directory.

Specifically, add after line 25 (the end of the path extraction block):

```fish
# If token is empty but previous token ends with /, we're completing inside that dir
if test -z "$token"
    set -l all_tokens (commandline -opc)
    if test (count $all_tokens) -ge 2
        set -l prev_token $all_tokens[-1]
        if string match -q -r '/$' -- "$prev_token"
            set -l expanded_prev (string replace -r '^~' $HOME -- "$prev_token")
            if test -d "$expanded_prev"
                set search_dir "$expanded_prev"
                set path_prefix "$prev_token"
                set query_part ""
            end
        end
    end
end
```

Also, in `__completion_config.fish`, add a guard in `__completion_get_type`: if `$token` is empty AND the last token in `commandline -opc` ends with `/` pointing to a valid directory AND the base command is in `$__cc_dir_cmds`, return "dirs" explicitly (before the "still typing command name" check on line 129 that might interfere). Actually, the current logic should already handle this correctly since count > 1 and token is empty skips line 129. But add a debug-friendly comment noting this path.

**Bug 2 Fix - Create missing Ctrl+Backspace/Delete functions:**

These 4 functions are bound in 06_keybindings.fish but were never implemented. Create them:

1. `custom_delete_backward_word.fish` - Ctrl+Backspace (slash-aware backward delete):
   - Get commandline text and cursor position
   - From cursor, scan backward to find the previous delimiter (/ or space)
   - Delete from that delimiter to cursor position (EXCLUDE the delimiter itself)
   - Per test spec section 3.1: `cd /home/rash/Documents/work|` + Ctrl+BS -> `cd /home/rash/Documents/|` (deletes "work", keeps "/")
   - If at a delimiter, skip past it and delete the segment before that
   - Use `commandline` to replace the text: `commandline -r` to set full line, `commandline -C` to set cursor

2. `custom_delete_backward_word_space.fish` - Ctrl+Shift+Backspace (space-only backward delete):
   - Same logic but ONLY space is a delimiter (slash is NOT a delimiter)
   - Per test spec section 4: deletes entire shell argument at a time
   - `git commit -m "fix bug" --amend|` + Ctrl+Shift+BS -> `git commit -m "fix bug" |`

3. `custom_delete_forward_word.fish` - Ctrl+Delete (slash-aware forward delete):
   - From cursor, scan forward to find the next delimiter (/ or space)
   - Delete from cursor to that delimiter (INCLUDE the delimiter)

4. `custom_delete_forward_word_space.fish` - Ctrl+Shift+Delete (space-only forward delete):
   - Same as above but only space is delimiter

Implementation pattern for all four functions:
```fish
function custom_delete_backward_word
    set -l cmd (commandline)
    set -l pos (commandline -C)

    if test $pos -eq 0
        return
    end

    # Text before cursor
    set -l before (string sub -l $pos -- "$cmd")
    set -l after (string sub -s (math $pos + 1) -- "$cmd")

    # Find the segment to delete: scan backward from end of $before
    # Skip trailing delimiter if cursor is right after one
    # Then delete back to the previous delimiter (or start of string)
    # Keep the delimiter

    # Use string regex to find: everything up to and including the last delimiter,
    # then the segment after it
    # Pattern: (prefix_with_delimiters)(segment_to_delete)
    if string match -q -r '^(.*[/ ])(.*?)$' -- "$before"
        # $before matched: group 1 = keep, group 2 = delete
        set -l keep (string replace -r '(.*[/ ]).*$' '$1' -- "$before")
        commandline -r -- "$keep$after"
        commandline -C (string length -- "$keep")
    else
        # No delimiter found - delete everything before cursor
        commandline -r -- "$after"
        commandline -C 0
    end
end
```

For the space-only variants, change the delimiter regex from `[/ ]` to just `[ ]` (space only).

For the forward variants, apply the same logic but scanning forward from cursor in `$after` and keeping the delimiter at the front of the remaining text.
  </action>
  <verify>
    Run `cd ~/.dotfiles && python setup.py` to apply symlinks.
    Then verify functions exist:
    - `fish -c "type custom_delete_backward_word"` should show function definition
    - `fish -c "type custom_delete_backward_word_space"` should show function definition
    - `fish -c "type custom_delete_forward_word"` should show function definition
    - `fish -c "type custom_delete_forward_word_space"` should show function definition
    - `fish -c "type __smart_tab_complete"` should show updated function with trailing-slash handling
  </verify>
  <done>
    All four custom_delete_*_word functions exist and are loadable by fish.
    __smart_tab_complete has trailing-slash fallback logic that sets search_dir from previous token when token is empty and previous token ends with /.
  </done>
</task>

<task type="auto">
  <name>Task 2: Add -- : = delimiters to Ctrl+Tab segment accept</name>
  <files>
    common/config/fish/functions/accept_next_path_segment.fish
  </files>
  <action>
Update `accept_next_path_segment.fish` to recognize additional delimiters beyond just `/` and space.

Per TAB-COMPLETION-TEST-SPEC.md section 2.2, Ctrl+Tab should stop at these delimiters:
- `/` (paths) -- already implemented
- space (args) -- already implemented
- `--` (flag prefix) -- NEW: stop AFTER accepting both dashes
- `:` (host:path, key:value) -- NEW
- `=` (assignments like --key=value) -- NEW
- Opening quote (`"` or `'`) -- NEW

Current implementation (lines 42-51) only checks for `/` and space. Add checks for the new delimiters.

Replace the delimiter checking section (after `commandline -f forward-single-char` and getting `$just_accepted`) with:

```fish
# Check delimiters - stop after accepting the delimiter character

# Slash delimiter (paths)
if test "$just_accepted" = "/"
    break
end

# Space delimiter (arguments)
if test "$just_accepted" = " "
    set found_word true
    break
end

# Colon delimiter (host:path, key:value)
if test "$just_accepted" = ":"
    break
end

# Equals delimiter (--key=value)
if test "$just_accepted" = "="
    break
end

# Opening quote delimiter
if test "$just_accepted" = '"' -o "$just_accepted" = "'"
    break
end

# Double-dash delimiter: if we just accepted a second '-' and the char before was also '-'
# This handles: `claude --` stopping at `claude --|`
# Check if the last two characters before cursor are "--"
set -l current_pos (commandline --cursor)
if test "$just_accepted" = "-" -a $current_pos -ge 2
    set -l current_text (commandline)
    set -l prev_char (string sub -s (math $current_pos - 1) -l 1 -- "$current_text")
    if test "$prev_char" = "-"
        # Check char before the first dash - should be space or start of token
        if test $current_pos -le 2
            break
        end
        set -l before_dashes (string sub -s (math $current_pos - 2) -l 1 -- "$current_text")
        if test "$before_dashes" = " "
            break
        end
    end
end
```

This ensures:
- `claude |--allow...` -> Ctrl+Tab -> `claude --|allow...` (stops after --)
- `scp server:|/home/...` -> stops after `:`
- `--key|=value` -> stops after `=`
- `git commit -m |"fix: bug"` -> stops after opening `"`
  </action>
  <verify>
    Run `cd ~/.dotfiles && python setup.py` to apply symlinks.
    `fish -c "type accept_next_path_segment"` should show updated function with new delimiter checks.
    Verify the function handles the test spec examples by checking the source code contains checks for "/", " ", ":", "=", quotes, and "--".
  </verify>
  <done>
    accept_next_path_segment.fish recognizes all 6 delimiter types: /, space, --, :, =, and opening quotes.
    The function stops after accepting each delimiter character per the test spec.
  </done>
</task>

</tasks>

<verification>
After both tasks complete:
1. `python setup.py` has been run to apply all changes
2. All 6 new/modified fish functions load without errors: `fish -c "type custom_delete_backward_word; type custom_delete_backward_word_space; type custom_delete_forward_word; type custom_delete_forward_word_space; type accept_next_path_segment; type __smart_tab_complete"` succeeds
3. No syntax errors in any modified fish files: `fish -n common/config/fish/functions/custom_delete_backward_word.fish` etc. for all files
</verification>

<success_criteria>
- cd with trailing-slash paths triggers fzf completion showing children of the target directory
- Ctrl+Backspace deletes previous path/word segment (slash-aware), keeping the delimiter
- Ctrl+Shift+Backspace deletes previous full argument (space-only delimiter)
- Ctrl+Delete and Ctrl+Shift+Delete delete forward segments with matching delimiter rules
- Ctrl+Tab stops at --, :, =, and opening quotes in addition to / and space
</success_criteria>

<output>
After completion, create `.planning/quick/13-fix-phase-02-tab-completion-bugs-1-cd-wi/13-SUMMARY.md`
</output>
