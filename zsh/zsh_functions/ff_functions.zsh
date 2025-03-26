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
    local preview_script
    preview_script=$(mktemp)
    cat > "$preview_script" << 'EOL'
#!/usr/bin/env bash
file="$1"
width="${2:-$((COLUMNS/2))}"
height="${3:-$((LINES/2))}"

if [[ -d "$file" ]]; then
    /usr/bin/eza --all --oneline --icons=always --color=always --group-directories-first "$file"
elif /usr/bin/file --mime-type "$file" | /usr/bin/grep -q image/; then
    /usr/bin/chafa --format symbols --size "${width}x${height}" --dither diffusion --dither-intensity 1.0 "$file"
elif /usr/bin/file --mime-type "$file" | /usr/bin/grep -q video/; then
    {
        thumb_file=$(mktemp --suffix=.jpg)
        /usr/bin/ffmpegthumbnailer -i "$file" -o "$thumb_file" -s 0 2>/dev/null
        /usr/bin/chafa --format symbols --size "${width}x$((height/2))" --dither diffusion --dither-intensity 1.0 "$thumb_file"
        rm -f "$thumb_file"
        echo -e "\n=== Video Information ===\n"
        /usr/bin/mediainfo --Inform="General;File: %FileName%.%FileExtension%\nSize: %FileSize/String%\nDuration: %Duration/String%\nFrame Rate: %FrameRate% fps" "$file"
        /usr/bin/mediainfo --Inform="Video;Resolution: %Width%x%Height%" "$file"
    }
else
    /usr/bin/bat --style=numbers --color=always --line-range :500 "$file" || /usr/bin/cat "$file"
fi
EOL
    chmod +x "$preview_script"

    local selection
    selection=$(/usr/bin/fd -H --follow --ignore-file "$temp_ignore" "${fd_args[@]}" 2>/dev/null | \
        command /usr/bin/fzf --height 40% --reverse --ansi \
            --preview-window "right:50%" \
            --preview "$preview_script {}" \
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
    action=$(command /usr/bin/fzf --prompt="Select action for $type: " --height=30% --reverse <<< $'open\nedit\ncopy\nyazi\npcmanfm\ncancel')

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
        edit) hx "$target" ;;
        copy) echo -n "$target" | wl-copy ;;
        yazi) yazi "$target" ;;
        pcmanfm)
            if [[ -d "$target" ]]; then
                pcmanfm "$target"
            else
                pcmanfm --select "$target"
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
    echo "  - edit       → hx"
    echo "  - copy       → wl-copy"
    echo "  - yazi       → open in yazi"
    echo "  - pcmanfm    → reveal in PCManFM"
    echo "  - cancel     → exit without action"
}
