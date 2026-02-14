# Smart context-aware Tab completion with fzf
# Delegates to modular completion engine with smart ordering and reasoning labels

function __smart_tab_complete
    set -l cmd (commandline -b)
    set -l token (commandline -t)
    set -l cursor_pos (commandline -C)

    # Extract path prefix and search base for relative/absolute paths
    set -l search_dir "."
    set -l path_prefix ""
    set -l query_part "$token"

    if string match -q -r '/' -- "$token"
        # Token contains a path - extract directory portion
        set path_prefix (string replace -r '[^/]*$' '' -- "$token")
        set query_part (string replace -r '.*/' '' -- "$token")
        if test -n "$path_prefix"
            # Expand tilde for directory test and search
            set -l expanded_path (string replace -r '^~' $HOME -- "$path_prefix")
            if test -d "$expanded_path"
                set search_dir "$expanded_path"
            end
        end
    end

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

    # === TRIGGER WORDS (existing functionality - unchanged) ===
    # fd triggers: fff, fdd, faa
    if string match -q -r '^f(ff|dd|aa)$' -- "$token"
        __fd_unified_widget
        return
    end

    # frecent triggers: ff, dd, aa
    switch "$token"
        case ff
            set -l result (frecent --files --interactive 2>/dev/null)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
        case dd
            set -l result (frecent --dirs --interactive 2>/dev/null)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
        case aa
            set -l result (frecent --all --interactive 2>/dev/null)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
    end

    # === CONTEXT DETECTION ===
    set -l comp_type (__completion_get_type)

    # === ROUTE BASED ON TYPE ===
    switch $comp_type

        case 'trigger:ff' 'trigger:dd' 'trigger:aa' 'trigger:fff' 'trigger:fdd' 'trigger:faa'
            # Already handled above, but catch in case context detection returns this
            commandline -f repaint
            return

        case native
            # Fish native completion for commands with no path context
            # This includes: empty line, git (without subcommand), docker, etc.
            commandline -f complete
            return

        case remote
            # Remote path completion via SSH
            __complete_remote_path
            return

        case dirs files both
            # === FZF-based completions with smart ordering ===

            # Generate ordered candidates with reasoning labels
            set -l candidates (__completion_order $comp_type "$search_dir" "$query_part")

            if test -z "$candidates"
                # No candidates - fall back to fish native
                commandline -f complete
                return
            end

            # fzf with preview toggle
            # Preview: Ctrl+P to toggle
            # For files: bat (if available) or cat
            # For dirs: eza (if available) or ls
            set -l preview_cmd
            switch $comp_type
                case files
                    if command -q bat
                        set preview_cmd 'bat --color=always --style=numbers {1}'
                    else
                        set preview_cmd 'cat {1}'
                    end
                case dirs
                    if command -q eza
                        set preview_cmd 'eza -la --color=always {1}'
                    else
                        set preview_cmd 'ls -lah {1}'
                    end
                case both
                    # Handle both files and dirs
                    if command -q bat; and command -q eza
                        set preview_cmd 'test -d {1} && eza -la --color=always {1} || bat --color=always --style=numbers {1}'
                    else
                        set preview_cmd 'test -d {1} && ls -lah {1} || cat {1}'
                    end
            end

            # fzf invocation with preview toggle
            # --delimiter=\t to split path from label
            # --with-nth=1,2 to show both path and label in main view
            # --nth=1 to search only in path (not label)
            # Ctrl+P to toggle preview
            set -l result (printf '%s\n' $candidates | \
                command fzf \
                    --height 40% \
                    --reverse \
                    --query "$query_part" \
                    --delimiter '\t' \
                    --with-nth 1,2 \
                    --nth 1 \
                    --preview "$preview_cmd" \
                    --preview-window 'right:50%:hidden' \
                    --bind 'ctrl-p:toggle-preview' \
                    --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff')

            if test -n "$result"
                # Extract just the path (before tab)
                set result (string split \t $result)[1]

                # Restore tilde prefix if user typed ~/...
                if string match -q '~*' -- "$path_prefix"
                    set result (string replace -r "^$HOME" '~' -- "$result")
                end

                # Escape spaces and special chars for shell
                set result (string replace -a ' ' '\\ ' -- "$result")
                commandline -t -- "$result"
            end
            commandline -f repaint

        case '*'
            # Unknown command: Try fish native first, then show files
            # Check if fish has completions for this command
            set -l tokens (commandline -xpc)
            set -l base_cmd $tokens[1]

            # Try native completion first
            set -l has_native_completion (complete -C "$cmd" | head -n 1)

            if test -n "$has_native_completion"
                # Fish knows about this command - use native
                commandline -f complete
                return
            else
                # Unknown command - show files only (not dirs)
                set -l candidates (__completion_order files "$search_dir" "$query_part")

                if test -z "$candidates"
                    commandline -f complete
                    return
                end

                set -l preview_cmd
                if command -q bat
                    set preview_cmd 'bat --color=always --style=numbers {1}'
                else
                    set preview_cmd 'cat {1}'
                end

                set -l result (printf '%s\n' $candidates | \
                    command fzf \
                        --height 40% \
                        --reverse \
                        --query "$query_part" \
                        --delimiter '\t' \
                        --with-nth 1,2 \
                        --nth 1 \
                        --preview "$preview_cmd" \
                        --preview-window 'right:50%:hidden' \
                        --bind 'ctrl-p:toggle-preview' \
                        --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff')

                if test -n "$result"
                    set result (string split \t $result)[1]
                    if string match -q '~*' -- "$path_prefix"
                        set result (string replace -r "^$HOME" '~' -- "$result")
                    end
                    set result (string replace -a ' ' '\\ ' -- "$result")
                    commandline -t -- "$result"
                end
                commandline -f repaint
            end
    end
end
