# Phase 02: fish-tab-autocomplete-robustness - Research

**Researched:** 2026-02-13
**Domain:** Fish shell completion systems, fzf integration, frecency algorithms
**Confidence:** MEDIUM-HIGH

## Summary

Fish shell Tab completion systems can be significantly enhanced by combining multiple completion sources (zoxide, fre, fish native completions, history, fd/ripgrep) through context-aware command detection. The current implementation already demonstrates many best practices (command categorization, fzf integration, trigger words), but opportunities exist for performance optimization, better source merging, remote path completion, and comprehensive testing.

The primary technical challenges are: (1) maintaining sub-100ms completion response times while merging multiple data sources, (2) implementing smart prioritization that respects both command intent and frecency scoring, (3) handling edge cases around path escaping and special characters, (4) creating comprehensive test coverage for all command contexts.

**Primary recommendation:** Build on Fish's native Rust-based completion system (4.0+) using native Fish functions for core logic, with optional Rust helpers for performance-critical operations like frecency scoring and large dataset filtering. Use fzf as the UI layer, leverage fish's built-in `complete` command for integration, and implement comprehensive littlecheck tests.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fish | 4.4.0+ | Shell environment | Rust-based (4.0+), native completion system, lazy loading |
| fzf | 0.51.0+ | Fuzzy selection UI | Battle-tested, fast (millions of items), fish integration via `fzf --fish` |
| fd | Latest | File/directory search | Faster than find, written in Rust, respects .gitignore |
| zoxide | Latest | Frecency-based directory jumping | Rust implementation, proven frecency algorithm (Mozilla-inspired) |
| fre | Latest | Frecency-based file tracking | Rust implementation, exponential decay algorithm |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ripgrep (rg) | Latest | Fast text search | Searching file contents for context-aware completion |
| carapace | Latest | Multi-shell completion generator | Generating completions for tools without native fish support |
| atuin | Latest | Enhanced shell history | SQLite-backed history with context metadata |
| based.fish | Latest | Context-aware completion plugin | Reference implementation for SQLite-backed suggestions |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| fzf | skim (sk) | Skim is Rust-native but less mature, smaller ecosystem |
| fd | find with optimizations | fd is simpler and faster out-of-box, but find has more features |
| Native fish functions | Python script | Python adds startup overhead (~10ms+), fish is lazy-loaded |
| Native fish functions | Rust binary | Rust is fastest but adds compilation complexity, use only for bottlenecks |

**Installation:**
```bash
# Arch Linux / pacman
sudo pacman -S fish fzf fd ripgrep

# fre and zoxide via cargo
cargo install fre zoxide

# Optional: carapace (multi-shell completions)
# Download from https://github.com/carapace-sh/carapace-bin/releases

# Optional: atuin (enhanced history)
cargo install atuin
```

## Architecture Patterns

### Recommended Project Structure
```
~/.config/fish/
├── functions/
│   ├── __smart_tab_complete.fish      # Main Tab handler (context detection)
│   ├── __shift_tab_complete.fish      # Shift+Tab handler (reverse/alternate)
│   ├── __completion_sources.fish      # Merges all sources with prioritization
│   ├── __frecency_merge.fish          # Combines zoxide + fre scores
│   ├── __remote_path_complete.fish    # SSH/SCP remote completion
│   └── __test_completion.fish         # Test helper function
├── completions/
│   └── [custom command completions]
├── conf.d/
│   ├── 06_keybindings.fish            # Bind Tab/Shift+Tab
│   └── 09_completions.fish            # Load completion configs
└── tests/
    └── completion_test.fish           # Littlecheck test file
```

### Pattern 1: Context-Aware Command Detection

**What:** Analyze command line to determine completion intent (files, dirs, both, remote)

**When to use:** For every Tab invocation to route to appropriate completion source

**Example:**
```fish
# Source: Current implementation + fish best practices
function __smart_tab_complete
    set -l cmd (commandline -b)        # Full buffer
    set -l token (commandline -t)      # Current token
    set -l tokens (commandline -xpc)   # Tokenized, cut at cursor

    # Extract base command (handle sudo/env wrappers)
    set -l base_cmd $tokens[1]
    if contains $base_cmd sudo doas env nohup
        set base_cmd $tokens[2]
    end

    # Categorize command intent
    if contains $base_cmd cd z pushd mkdir
        __complete_directories
    else if contains $base_cmd nvim vim cat bat
        __complete_files
    else if contains $base_cmd cp mv rsync
        __complete_both
    else if string match -q '*:*' -- "$token"
        __complete_remote_path
    else
        commandline -f complete  # Fall back to native
    end
end
```

### Pattern 2: Multi-Source Merging with Prioritization

**What:** Combine results from zoxide, fre, history, fd, and fish completions with smart ranking

**When to use:** After determining command intent, before presenting to fzf

**Example:**
```fish
# Conceptual - demonstrates prioritization logic
function __merge_completion_sources --argument-names context query
    set -l results

    # Source 1: Frecency (highest priority for known patterns)
    if test "$context" = "dirs"
        set -a results (zoxide query -l | head -n 20)
    else if test "$context" = "files"
        set -a results (fre --sorted | head -n 20)
    end

    # Source 2: Fish native completions (for current command)
    set -a results (complete -C"$query" | cut -f1)

    # Source 3: Filesystem (for novel paths)
    set -a results (fd --type $context --max-depth 3 ".*$query" | head -n 100)

    # Source 4: History (command-specific)
    # Extract paths from history for this command

    # Deduplicate while preserving order (keeps first/highest priority)
    printf '%s\n' $results | awk '!seen[$0]++'
end
```

### Pattern 3: Remote Path Completion via SSH

**What:** Execute `ls` on remote host to provide path completions for scp/rsync

**When to use:** When token contains `:` separator (host:path format)

**Example:**
```fish
# Source: Adapted from fish-shell/share/completions/scp.fish
function __complete_remote_path
    set -l token (commandline -t)

    # Parse host:path format
    if string match -qr '(.+):(.*)' -- "$token"
        set -l remote_host $match[1]
        set -l remote_path $match[2]

        # Execute remote ls via SSH with BatchMode (no prompts)
        set -l results (ssh -o "BatchMode yes" "$remote_host" \
            command ls -dp "$remote_path"'*' 2>/dev/null)

        if test -n "$results"
            # Escape results and prepend host:
            for result in $results
                echo "$remote_host:"(string escape "$result")
            end | fzf --height 40% --reverse --query "$remote_path"
        end
    end
end
```

### Pattern 4: Shift+Tab for Reverse/Alternate Completion

**What:** Provide reverse navigation in completion pager OR alternate completion mode

**When to use:** User presses Shift+Tab instead of Tab

**Example:**
```fish
# Two approaches:
# 1. Native fish pager reverse (simplest)
bind \e[Z complete  # Shift+Tab triggers pager in reverse mode

# 2. Custom alternate mode (e.g., show ALL sources instead of prioritized)
function __shift_tab_complete
    set -l token (commandline -t)

    # Show comprehensive results from all sources (no prioritization)
    __merge_all_sources $token | fzf --height 40% --reverse
end
```

### Anti-Patterns to Avoid

- **Synchronous blocking for slow operations:** Always use timeouts or background jobs for network/slow disk operations. Example: `ssh` with `-o ConnectTimeout=2` to prevent hangs.

- **Over-reliance on external commands in hot path:** Each `fd` or `zoxide` call adds ~10-50ms. Cache results when token hasn't changed, use `test -v` to check variable existence.

- **Ignoring escaping edge cases:** Paths with spaces/special chars MUST be escaped. Use `string escape` or Fish's native quoting. Test with: `test\ file.txt`, `file (2).mp4`, `$weird[name]`.

- **Not respecting user's completion state:** If user has typed `cd ~/Doc` and Tab completes to `~/Documents/`, don't clear the partially-matched prefix. Use `commandline -t -- $result` not `commandline -r`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Frecency scoring | Custom visit tracking | zoxide/fre | Exponential decay, time-bucketing, proven algorithms, edge case handling (symlinks, deleted dirs) |
| Fuzzy matching UI | Custom fzf alternative | fzf (or skim) | Handles millions of items, async rendering, preview panes, tested across terminals |
| Shell-agnostic completions | Per-shell scripts | Carapace | Generates for 11+ shells from single spec, cobra integration |
| Path completion from SSH | Custom SFTP wrapper | Fish's `__scp_remote_target` pattern | Handles batch mode, port mapping, path escaping, error suppression |
| Command-line parsing | Manual string splitting | `commandline -xpc`, `commandline -t` | Respects quoting, handles edge cases, escaping-aware |
| Completion testing | Manual interactive tests | Littlecheck framework | Deterministic, fast, CI-compatible, self-documenting |

**Key insight:** Completion systems have deceptive complexity around escaping, quoting, terminal compatibility, and race conditions. Leverage Fish's battle-tested primitives and proven external tools rather than reimplementing.

## Common Pitfalls

### Pitfall 1: Performance Degradation with Large Datasets

**What goes wrong:** Completion takes >200ms, feels sluggish, blocks typing

**Why it happens:**
- Running `fd` without `--max-depth` on large directory trees
- Not limiting zoxide/fre result counts
- Processing thousands of history entries without filtering
- Using `find` instead of `fd`
- Multiple sequential external commands (additive latency)

**How to avoid:**
- Set hard limits: `fd --max-depth 3`, `zoxide query -l | head -n 50`
- Use fzf's streaming mode for large datasets
- Profile with `fish --profile` to identify bottlenecks
- Cache results when token prefix hasn't changed
- Run expensive operations in background with timeout

**Warning signs:**
- Tab completion noticeable lag (>100ms)
- Terminal freezes briefly
- Completion slower on certain directories (network mounts, large repos)

### Pitfall 2: Escaping/Quoting Breakage

**What goes wrong:** Completions break with spaces, quotes, special characters (`$`, `[`, `)`, etc.)

**Why it happens:**
- Using raw strings instead of `string escape`
- Mixing quoting styles inconsistently
- Not handling pre-escaped input
- Passing unescaped paths to `commandline -t`

**How to avoid:**
- ALWAYS use `string escape` or `string escape -n` for paths
- Test completion with: `file with spaces.txt`, `file[1].txt`, `$var.txt`, `"quoted.txt`
- For remote paths: double-escape (local shell + remote shell)
- Use `commandline -t -- (string escape "$result")` pattern

**Warning signs:**
- Completions work for simple names, fail for complex ones
- Error messages about "unexpected tokens"
- Completions insert backslashes incorrectly

### Pitfall 3: Context Detection False Positives

**What goes wrong:** `nvim +Tab` shows directories when you want files, `cd +Tab` shows files

**Why it happens:**
- Not handling command aliases/functions
- Missing common commands in categorization lists
- Not detecting subcommands (e.g., `git add` vs `git log`)
- Wrapper commands (sudo, env) not stripped properly

**How to avoid:**
- Maintain comprehensive command lists (files-only, dirs-only, both)
- Handle wrappers: `sudo`, `doas`, `env`, `nohup`, `nice`, `time`, `watch`, `strace`
- For git: check `$tokens[2]` for subcommand, categorize separately
- Provide fallback to native `complete` when uncertain
- Use xdg-mime for file type detection (open, xdg-open)

**Warning signs:**
- Wrong completion type for known commands
- New commands installed not getting appropriate completions
- Git subcommands all treated identically

### Pitfall 4: Shift+Tab UX Confusion

**What goes wrong:** Users press Shift+Tab expecting reverse navigation but get unexpected behavior

**Why it happens:**
- Custom Shift+Tab handler conflicts with fish native pager
- Trigger words (`ff`, `dd`) consume Shift+Tab as Tab
- No visual feedback for alternate mode

**How to avoid:**
- If using custom Shift+Tab: document clearly, provide escape hatch to native behavior
- Recommended: Use fish native pager reverse (bind `\e[Z` to pager navigation)
- For trigger words: detect Shift+Tab separately if possible, or rely on pager
- Test Shift+Tab in multiple contexts: empty line, mid-word, after completion

**Warning signs:**
- User confusion about "what does Shift+Tab do here?"
- Inconsistent behavior between bare completion and trigger words
- No way to reverse through native fish completions

### Pitfall 5: Remote Completion Hangs/Failures

**What goes wrong:** `scp remote:+Tab` hangs for 30+ seconds or never completes

**Why it happens:**
- SSH host unreachable, no timeout set
- SSH asks for password (BatchMode not enabled)
- Remote host runs fish with greeting that breaks ls output
- Path escaping differs between local and remote

**How to avoid:**
- ALWAYS use `ssh -o "BatchMode yes" -o "ConnectTimeout=2"`
- Redirect stderr: `2>/dev/null` to suppress prompts
- Test remote completion with unreachable hosts to verify timeout
- For remote fish: ensure `fish_greeting` is empty or redirected
- Consider caching remote ls results for ~5 seconds

**Warning signs:**
- Terminal hangs on Tab after typing `host:`
- Password prompts during completion
- Error messages from remote shell printed to local terminal

### Pitfall 6: Race Conditions with Async Operations

**What goes wrong:** Completions show stale results or duplicate entries

**Why it happens:**
- Multiple Tab presses trigger parallel completion commands
- Background jobs update database while reading
- fzf query changes faster than source data updates

**How to avoid:**
- Use job control to cancel previous incomplete operation on new Tab
- For databases (zoxide, fre): reads are safe, writes need locking
- Debounce rapid Tab presses (fish handles this natively, don't override)
- Test by pressing Tab rapidly 10+ times

**Warning signs:**
- Different results for same query when Tab pressed twice
- Completions "flash" or change unexpectedly
- Database corruption errors

## Code Examples

Verified patterns from official sources and current implementation:

### Pattern 1: Basic Completion Widget Structure

```fish
# Source: Fish documentation + current implementation
function __my_completion_widget
    # 1. Gather context
    set -l buffer (commandline -b)      # Whole command line
    set -l token (commandline -t)       # Current token
    set -l tokens (commandline -xpc)    # Parsed tokens, cut at cursor

    # 2. Determine what to complete
    set -l base_cmd (basename $tokens[1])

    # 3. Generate candidates
    set -l candidates
    switch $base_cmd
        case nvim vim
            set candidates (fd -t f)
        case cd
            set candidates (zoxide query -l)
        case '*'
            commandline -f complete  # Fallback
            return
    end

    # 4. Select with fzf
    set -l result (printf '%s\n' $candidates | fzf --height 40% --reverse --query "$token")

    # 5. Insert result (escaped)
    if test -n "$result"
        commandline -t -- (string escape "$result")
    end

    # 6. Repaint
    commandline -f repaint
end
```

### Pattern 2: Using Fish's Complete Command for Prioritization

```fish
# Source: https://fishshell.com/docs/current/cmds/complete.html
# Define completions with explicit ordering using --keep-order

# High priority: recent files from fre
complete -c nvim -f -k -a '(fre --sorted --files | head -n 10)'

# Medium priority: files in current directory
complete -c nvim -f -k -a '(fd -t f --max-depth 1)'

# Low priority: all files recursively
complete -c nvim -f -a '(fd -t f --max-depth 3)'

# Note: Multiple complete calls with -k show later ones FIRST
# So define in reverse priority order (low to high)
```

### Pattern 3: Frecency Score Merging

```fish
# Conceptual - demonstrates zoxide's frecency algorithm
# Source: https://github.com/ajeetdsouza/zoxide/wiki/Algorithm

function __calculate_frecency --argument-names score last_access
    set -l now (date +%s)
    set -l age (math "$now - $last_access")

    # Time-based multipliers (zoxide algorithm)
    if test $age -lt 3600  # Last hour
        math "$score * 4"
    else if test $age -lt 86400  # Last day
        math "$score * 2"
    else if test $age -lt 604800  # Last week
        math "max(1, $score / 2)"
    else  # Older
        math "max(1, $score / 4)"
    end
end
```

### Pattern 4: Remote Path Completion

```fish
# Source: Adapted from https://github.com/fish-shell/fish-shell/blob/master/share/completions/scp.fish

function __scp_remote_path
    set -l token (commandline -t)

    # Parse user@host:/path format
    if string match -qr '^([^:]+):(.*)$' -- "$token"
        set -l remote_target $match[1]
        set -l remote_path $match[2]
        set -l path_prefix (string replace -r '[^/]*$' '' -- "$remote_path")

        # Execute remote ls with safety flags
        set -l results (ssh -o "BatchMode yes" \
                           -o "ConnectTimeout=2" \
                           "$remote_target" \
                           command ls -dp "$path_prefix"'*' 2>/dev/null)

        # Format and return
        for result in $results
            echo "$remote_target:$result"
        end
    end
end

# Use in completion
complete -c scp -f -a '(__scp_remote_path)'
```

### Pattern 5: Testing Completions with Littlecheck

```fish
# Source: https://fishshell.com/docs/current/contributing.html
# File: ~/.config/fish/tests/completion_test.fish

# RUN: %fish %s

# Test directory completion for cd
complete -C'cd /tm'
# CHECK: /tmp/

# Test file completion for nvim
complete -C'nvim test'
# CHECK: test_file.txt

# Test escaping with spaces
mkdir -p "/tmp/test space"
complete -C'cd /tmp/test'
# CHECK: /tmp/test\ space/

# Cleanup
rm -rf "/tmp/test space"
```

### Pattern 6: Keybinding Integration

```fish
# Source: Current implementation + Fish documentation

# Tab: Smart context-aware completion
bind -M insert \t __smart_tab_complete
bind -M default \t __smart_tab_complete

# Shift+Tab: Use native pager reverse navigation
# (Fish handles this automatically in pager mode)

# Alternative: Custom Shift+Tab handler
# bind -M insert \e[Z __shift_tab_complete

# Ctrl+F: Frecent file picker (existing pattern)
bind -M insert \cf insert_fre_file

# Ctrl+D: Zoxide directory picker (existing pattern)
bind -M insert \cd insert_zoxide_dir
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| C++ implementation | Rust implementation | Fish 4.0 (2025) | Better concurrency, easier async features, improved safety |
| Manual completion scripts | Auto-generated from man pages | Fish 2.0+ | Reduced maintenance, broader coverage |
| Alphabetical sorting only | `--keep-order` flag | Fish 3.0+ | Allows frecency-based prioritization |
| find for file search | fd as standard | Community shift ~2020 | 10-50x faster, respects .gitignore |
| Bash completion wrappers | Carapace multi-shell | 2022+ | Single source for all shells |
| grep for history search | atuin SQLite backend | 2023+ | Context metadata, sync across machines |
| Synchronous completion | Async in progress | Fish 4.x roadmap | Non-blocking completions (future) |

**Deprecated/outdated:**
- **Bash completion bridge:** Fish 3.0+ has better native support, bash wrapper adds overhead
- **`__fish_complete_path`:** Still works but `fd` with fzf is more flexible and faster
- **Manual frecency tracking:** Use zoxide or fre instead of custom scoring
- **apropos for man page completion:** Switched to fish_update_completions (faster)

## Open Questions

1. **Performance threshold for "acceptable" completion**
   - What we know: Users notice >100ms lag, prefer <50ms
   - What's unclear: Optimal tradeoff between completeness vs speed (show 20 or 200 results?)
   - Recommendation: Benchmark current implementation, set hard limit at 100ms, tune result counts to meet target

2. **Remote completion reliability**
   - What we know: SSH timeouts needed, BatchMode prevents hangs
   - What's unclear: Should we cache remote ls results? For how long?
   - Recommendation: Implement 5-second cache per remote host:path prefix, clear on new SSH session

3. **Merge strategy for conflicting sources**
   - What we know: Frecency should rank high, but novel paths need discoverability
   - What's unclear: Exact weighting when zoxide and fd both return same path
   - Recommendation: Deduplicate, prefer frecency source, but boost fd results that match typed prefix

4. **xdg-mime integration scope**
   - What we know: xdg-mime can determine file types, file -i for heuristics
   - What's unclear: Is MIME detection too slow for completion? Which commands benefit?
   - Recommendation: Prototype for `open` and `xdg-open` commands, measure overhead. Only expand if <10ms impact.

5. **Testing coverage breadth**
   - What we know: Littlecheck enables deterministic testing
   - What's unclear: How to test fzf integration without interactive terminal?
   - Recommendation: Test completion candidate generation (before fzf) with littlecheck, use tmux/pexpect for end-to-end interactive tests

6. **Async completion feasibility**
   - What we know: Fish 4.0 Rust port enables async, not yet implemented for completions
   - What's unclear: Can we use background jobs to pre-populate completion cache?
   - Recommendation: Monitor fish-shell issue #2501 for official async support. For now, use aggressive caching and timeouts.

## Sources

### Primary (HIGH confidence)

- [Fish Shell 4.4.0 Documentation - Writing Completions](https://fishshell.com/docs/current/completions.html) - Completion system architecture, `complete` command usage
- [Fish Shell 4.4.0 Documentation - complete command](https://fishshell.com/docs/current/cmds/complete.html) - Flags, options, `--keep-order` behavior
- [Fish Shell 4.4.0 Documentation - commandline command](https://fishshell.com/docs/current/cmds/commandline.html) - Widget development, buffer manipulation
- [Fish Shell GitHub - scp.fish](https://github.com/fish-shell/fish-shell/blob/master/share/completions/scp.fish) - Remote path completion implementation
- [fzf GitHub Repository](https://github.com/junegunn/fzf) - Official fzf features, shell integration via `fzf --fish`
- [Zoxide GitHub - Algorithm Wiki](https://github.com/ajeetdsouza/zoxide/wiki/Algorithm) - Frecency scoring formula, time buckets
- [fre GitHub Repository](https://github.com/camdencheek/fre) - Exponential decay algorithm for files
- [Carapace GitHub Repository](https://github.com/carapace-sh/carapace) - Multi-shell completion generation

### Secondary (MEDIUM confidence)

- [PatrickF1/fzf.fish Plugin](https://github.com/PatrickF1/fzf.fish) - Fish+fzf integration patterns, performance practices
- [Fish Shell Performance Tips](https://erika.florist/wiki/linux/shellperformance/) - Profiling, lazy loading, optimization strategies
- [Fish Shell Issue #2501](https://github.com/fish-shell/fish-shell/issues/2501) - Async completion discussions
- [Fish Shell Issue #6592](https://github.com/fish-shell/fish-shell/issues/6592) - Autocompletion performance issues
- [Atuin Documentation](https://atuin.sh/) - Shell history with SQLite, context tracking
- [based.fish GitHub](https://github.com/Edu4rdSHL/based.fish) - Context-aware completion reference implementation
- [ripgrep Blog - Performance Analysis](https://burntsushi.net/ripgrep/) - Benchmark comparisons vs grep/ag/ack
- [Fish Shell 4.0 Rust Port Blog](https://fishshell.com/blog/rustport/) - Rust migration motivations, concurrency benefits

### Tertiary (LOW confidence - marked for validation)

- [Medium - Zsh vs Fish Comparison](https://medium.com/@awaleedpk/zsh-vs-fish-the-ultimate-shell-showdown-for-2025-27b89599859b) - General performance comparisons (needs benchmarking validation)
- [XDG MIME Applications - ArchWiki](https://wiki.archlinux.org/title/XDG_MIME_Applications) - MIME type integration (needs performance testing in completion context)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official docs, proven tools in production use
- Architecture: HIGH - Patterns extracted from official implementations and current codebase
- Pitfalls: MEDIUM-HIGH - Mix of documented issues and inferred edge cases
- Performance: MEDIUM - Benchmarks exist for tools (fd, fzf, ripgrep) but not holistic completion system
- Remote completion: MEDIUM - Implementation exists but edge cases (caching, auth) need validation
- Testing: MEDIUM - Littlecheck documented, but fzf integration testing approach unclear

**Research date:** 2026-02-13
**Valid until:** 2026-03-13 (30 days - fish shell stable, tools mature)

**Key unknowns requiring prototyping:**
1. Exact performance characteristics of merged completion sources (need benchmarking)
2. Remote completion caching strategy effectiveness
3. fzf integration testing methodology
4. Optimal result count limits per source
5. xdg-mime overhead in completion context
