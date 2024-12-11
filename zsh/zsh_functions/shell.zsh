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
    if [[ "$1" == "--help" ]]; then
        echo "Usage: ff [search_term]"
        echo "Search for files containing search_term in their name and open selected files"
        echo ""
        echo "Options:"
        echo "  --help    Show this help message"
        return 0
    fi

    local selections
    if sudo -v; then
        # Build find exclusion patterns from ignore.conf
        local exclude_patterns=()
        while IFS= read -r pattern; do
            [[ -z "$pattern" ]] && continue  # Skip empty lines
            exclude_patterns+=("-path" "$pattern" "-prune" "-o")
        done < "${XDG_CONFIG_HOME}/search/ignore.conf"

        # Build find inclusion patterns from include.conf
        local include_patterns=()
        while IFS= read -r pattern; do
            [[ -z "$pattern" ]] && continue  # Skip empty lines
            include_patterns+=("-o" "-path" "$pattern")
        done < "${XDG_CONFIG_HOME}/search/include.conf"

        # Start find and pipe its output directly to fzf
        selections=$(sudo find / "(" "${exclude_patterns[@]}" "-false" ")" "${include_patterns[@]}" "-o" "-iname" "*$1*" "-print" 2>/dev/null | \
            command fzf --multi --preview 'bat --color=always {}' \
            --preview-window '~3' \
            --color 'fg:#cdd6f4,fg+:#cdd6f4,bg:#1e1e2e,preview-bg:#1e1e2e,border:#89b4fa')

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

rr_f() {
  # Define log file location
  local log_file="$HOME/.rrf_log"

  # Redirect stdout and stderr to the log file
  exec > >(tee -a "$log_file") 2>&1

  # Get the monitor index of the active window
  local monitor_index=$(hyprctl activewindow -j | jq '.monitor')

  # Get workspace ID of the active window
  local workspace_id=$(hyprctl activewindow -j | jq '.workspace.id')

  # Determine the axis to use based on the monitor index
  if [[ "$monitor_index" -eq 0 ]]; then
    # Horizontal monitor
    local master_address=$(hyprctl clients -j | jq "[.[] | select (.workspace.id == $workspace_id)] | min_by(.at[0]) | .address")
  else
    # Vertical monitor
    local master_address=$(hyprctl clients -j | jq "[.[] | select (.workspace.id == $workspace_id)] | min_by(.at[1]) | .address")
  fi

  # Get the address of the active window
  local active_address=$(hyprctl activewindow -j | jq '.address')

  # Compare the active window address with the master window address
  if [[ "$active_address" == "$master_address" ]]; then
    echo "The active window is the master window."

    # Launch Alacritty, clear terminal output, and disown it
    alacritty -e zsh -c "sleep 0.2; reset; exec zsh" & new_pid=$!
    disown

    # Wait explicitly for the new Alacritty window to be the active window
    for i in {1..10}; do
      sleep 0.1
      current_active=$(hyprctl activewindow -j | jq '.address')
      if [[ "$current_active" != "$active_address" ]]; then
        break
      fi
    done

    # Now swap with master after the new terminal is the active window
    hyprctl dispatch layoutmsg swapwithmaster
  else
    echo "The active window is not the master window."
    # Launch Alacritty, clear terminal output, and disown it
    alacritty -e zsh -c "clear; reset; exec zsh" & disown
  fi

  # Exit the current terminal
  exit
}
