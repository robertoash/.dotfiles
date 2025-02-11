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
  # Define the path to your custom exclude patterns file
  local exclude_file="$HOME/.config/fd/.fdignore"

  # Check if the exclude file exists
  if [[ -f "$exclude_file" ]]; then
    # Read each line (pattern) from the exclude file into an array
    local excludes=()
    while IFS= read -r pattern || [[ -n "$pattern" ]]; do
      # Skip empty lines and comments
      [[ -z "$pattern" || "$pattern" =~ ^# ]] && continue
      excludes+=(--exclude "$pattern")
    done < "$exclude_file"
  fi

  # Check if a search query was provided
  local query="$1"

  # Use fd to list all files and directories, excluding specified patterns
  # Pipe the results to fzf for fuzzy selection
  local selection
  if [[ -n "$query" ]]; then
    selection=$(fd -H --type f --type d "${excludes[@]}" "$query" ~ 2>/dev/null | \
      fzf --height 40% --reverse --preview 'bat --style=numbers --color=always {} || cat {}')
  else
    selection=$(fd --type f --type d "${excludes[@]}" ~ 2>/dev/null | \
      fzf --height 40% --reverse --preview 'bat --style=numbers --color=always {} || cat {}')
  fi

  # If no selection was made, exit the function
  [[ -z "$selection" ]] && return

  # Determine if the selected item is a directory
  if [[ -d "$selection" ]]; then
    # Change to the selected directory
    cd "$selection" || return
  else
    # Open the selected file with xdg-open
    xdg-open "$selection"
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
