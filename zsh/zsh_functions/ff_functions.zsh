ff() {
    local temp_ignore=$(load_fd_excludes)
    local default_search_path="$HOME"
    local search_path=""
    local search_pattern=""

    # Argument parsing
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        ff_help
        return
    fi

    if [[ $# -eq 0 ]]; then
        search_path="$default_search_path"
        search_pattern=""
    elif [[ $# -eq 1 ]]; then
        if [[ -d "$1" ]]; then
            search_path="$1"
            search_pattern=""
        else
            search_path="$default_search_path"
            search_pattern="$1"
        fi
    elif [[ $# -eq 2 ]]; then
        if [[ -d "$1" ]]; then
            search_path="$1"
            search_pattern="$2"
        elif [[ -d "$2" ]]; then
            search_path="$2"
            search_pattern="$1"
        else
            echo "❌ Error: One of the arguments must be a valid path" >&2
            ff_help
            return 1
        fi
    else
        echo "❌ Too many arguments." >&2
        ff_help
        return 1
    fi

    # Proper fd arg ordering
    local fd_args=()
    if [[ -n "$search_pattern" && -n "$search_path" ]]; then
        fd_args=("$search_pattern" "$search_path")
    elif [[ -n "$search_pattern" ]]; then
        fd_args=("$search_pattern")
    elif [[ -n "$search_path" ]]; then
        fd_args=("" "$search_path")
    else
        fd_args=("" "$default_search_path")
    fi

    # Create a preview script with proper terminal handling

    local selection
    selection=$(/usr/bin/fd -H --follow --ignore-file "$temp_ignore" "${fd_args[@]}" 2>/dev/null | \
        command /usr/bin/fzf --height 40% --reverse --ansi \
            --preview-window "right:50%" \
            --preview '$HOME/.config/fzf/fzf_preview.sh {}' \
            --preview-window "~3")

    rm -f "$preview_script"

    if [[ -z "$selection" ]]; then
        echo "No item selected." >&2
        rm -f "$temp_ignore"
        return 1
    fi

    if [[ ! -e "$selection" ]]; then
        echo "❌ Error: Selected path does not exist: $selection" >&2
        rm -f "$temp_ignore"
        return 1
    fi

    local type="file"
    [[ -d "$selection" ]] && type="dir"

    local action
    if [[ "$type" == "dir" ]]; then
        action=$(command /usr/bin/fzf --prompt="Select action for directory: " --height=30% --reverse <<< $'cd\nyazi\npcmanfm\nedit\ncopy-path\ncancel')
    else
        action=$(command /usr/bin/fzf --prompt="Select action for file: " --height=30% --reverse <<< $'open\nedit\ncopy-path\nyazi\npcmanfm\ncancel')
    fi

    if [[ "$action" == "cancel" || -z "$action" ]]; then
        echo "No action selected." >&2
        rm -f "$temp_ignore"
        return 1
    fi

    rm -f "$temp_ignore"
    perform_ff_action "$selection" "$action"
}


perform_ff_action() {
    local target="$1"
    local mode="$2"

    case "$mode" in
        open) xdg-open "$target" ;;
        edit) nvim "$target" ;;
        copy-path)
            if [[ -d "$target" ]]; then
                # For directories, copy the path with a trailing slash to indicate it's a directory
                echo -n "${target%/}/" | wl-copy
            else
                # For files, copy the full path
                echo -n "$target" | wl-copy
            fi
            ;;
        yazi) yazi "$target" ;;
        pcmanfm)
            if [[ -d "$target" ]]; then
                pcmanfm "$target"
            else
                pcmanfm --select "$target"
            fi
            ;;
        cd)
            if [[ -d "$target" ]]; then
                cd "$target"
            else
                echo "❌ Error: Cannot cd into a file" >&2
                return 1
            fi
            ;;
        *) echo "Unknown action: $mode" >&2; return 1 ;;
    esac
}

load_fd_excludes() {
    local exclude_file="$HOME/.config/fd/.fdignore"
    local temp_ignore
    temp_ignore=$(mktemp)

    if [[ -f "$exclude_file" ]]; then
        # Copy existing patterns and ensure they work with full paths
        while IFS= read -r pattern || [[ -n "$pattern" ]]; do
            [[ -z "$pattern" || "$pattern" == \#* ]] && continue
            echo "$pattern" >> "$temp_ignore"
        done < "$exclude_file"
    fi

    echo "$temp_ignore"
}


ff_help() {
    echo "Usage: ff [search_string] [search_path]"
    echo
    echo "Examples:"
    echo "  ff                         → search everything in \$HOME"
    echo "  ff notes                   → search for 'notes' under \$HOME"
    echo "  ff ~/projects              → search all in that path"
    echo "  ff todo ~/dev              → search for 'todo' in ~/dev"
    echo
    echo "After selection, choose an action:"
    echo "  - open       → xdg-open"
    echo "  - edit       → nvim"
    echo "  - copy       → wl-copy"
    echo "  - yazi       → open in yazi"
    echo "  - pcmanfm    → reveal in PCManFM"
    echo "  - cancel     → exit without action"
}
