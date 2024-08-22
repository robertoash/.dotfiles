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
    sudo find / -iname "$1" 2>/dev/null
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



