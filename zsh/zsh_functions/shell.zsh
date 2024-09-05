# Function to get the last N-th unique directory from the command history
lld() {
    local index=${1:-1}  # Default index is 1 if no argument is provided
    local last_dirs=()
    local last_dir=""
    local cmd

    # Process history to extract directories, ignoring duplicates and handling '~'
    history -n 1 | tac | while read -r cmd; do
        local paths=$(echo "$cmd" | grep -Eo '([~]?/[^ ]+/?)')
        for dir in $paths; do
            if [[ "$dir" != "$last_dir" ]] && process_path "$dir" "dir"; then
                last_dirs+=("$dir")
                last_dir="$dir"
                if (( ${#last_dirs[@]} == index )); then
                    break 2
                fi
            fi
        done
    done

    if (( index > ${#last_dirs[@]} )); then
        echo "No such directory in history"
    else
        eval echo "${last_dirs[$index]}"
    fi
}

# Function to get the last N-th unique file from the command history
llf() {
    local index=${1:-1}  # Default index is 1 if no argument is provided
    local last_files=()
    local last_file=""
    local cmd

    # Process history to extract files, ignoring duplicates and handling '~'
    history -n 1 | tac | while read -r cmd; do
        local paths=$(echo "$cmd" | grep -Eo '([~]?/[^ ]+/?)')
        for file in $paths; do
            if [[ "$file" != "$last_file" ]] && process_path "$file" "file"; then
                last_files+=("$file")
                last_file="$file"
                if (( ${#last_files[@]} == index )); then
                    break 2
                fi
            fi
        done
    done

    if (( index > ${#last_files[@]} )); then
        echo "No such file in history"
    else
        eval echo "${last_files[$index]}"
    fi
}

# Shortcut to find a file anywhere by name
ff() {
    local selections
    if sudo -v; then
        # Start find and pipe its output directly to fzf
        selections=$(sudo find / -path "*/.snapshots" -prune -o -iname "*$1*" -print 2>/dev/null | \
            command fzf --tac --multi --preview 'bat --color=always {}' \
            --preview-window '~3' \
            --color 'fg:#cdd6f4,fg+:#cdd6f4,bg:#1e1e2e,preview-bg:#1e1e2e,border:#89b4fa' &)

        # Get the PID of the find command
        find_pid=$!

        # Kill the find process if it's still running
        trap 'kill $find_pid 2>/dev/null' EXIT

        if [ -n "$selections" ]; then
            echo "$selections" | while IFS= read -r file; do
                xdg-open "$file" &
            done
        fi
    else
        echo "Sudo authentication failed. Unable to search system-wide."
    fi
}

# Launch apps in a specific workspace
in_ws() {
  local workspace_number=$1
  shift
  local command="$@"

  # Start the job with a descriptive name
  ( eval "$command") &

  # Wait briefly to allow the window to open
  sleep 0.5

  # Move the most recently focused window to the specified workspace
  hyprctl dispatch movetoworkspace $workspace_number
}



