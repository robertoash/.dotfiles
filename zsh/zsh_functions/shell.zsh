# Search for files only
fff() {
  local exclude_file="$HOME/.config/fd/.fdignore"
  local excludes=()

  if [[ -f "$exclude_file" ]]; then
    while IFS= read -r pattern || [[ -n "$pattern" ]]; do
      [[ -z "$pattern" || "$pattern" =~ ^# ]] && continue
      excludes+=(--exclude "$pattern")
    done < "$exclude_file"
  fi

  local search_pattern=""
  local search_path="$HOME"  # Default to searching in home directory

  if [[ $# -eq 2 ]]; then
    search_pattern="$1"
    search_path="$2"
  elif [[ $# -eq 1 ]]; then
    if [[ "$1" == "." ]]; then
      search_path="."
    else
      search_pattern="$1"
    fi
  fi

  local selection
  selection=$(fd -H --type f --follow "${excludes[@]}" "$search_pattern" "$search_path" 2>/dev/null | \
    fzf --height 40% --reverse --preview 'bat --style=numbers --color=always {} || cat {}')

  [[ -z "$selection" ]] && return
  xdg-open "$selection"
}

# Search for directories only
ffd() {
  local exclude_file="$HOME/.config/fd/.fdignore"
  local excludes=()

  if [[ -f "$exclude_file" ]]; then
    while IFS= read -r pattern || [[ -n "$pattern" ]]; do
      [[ -z "$pattern" || "$pattern" =~ ^# ]] && continue
      excludes+=(--exclude "$pattern")
    done < "$exclude_file"
  fi

  local search_pattern=""
  local search_path="$HOME"  # Default to searching in home directory

  if [[ $# -eq 2 ]]; then
    search_pattern="$1"
    search_path="$2"
  elif [[ $# -eq 1 ]]; then
    if [[ "$1" == "." ]]; then
      search_path="."
    else
      search_pattern="$1"
    fi
  fi

  local selection
  selection=$(fd -H --type d --follow "${excludes[@]}" "$search_pattern" "$search_path" 2>/dev/null | \
    fzf --height 40% --reverse --preview 'eza -1 --color=always {}')

  [[ -z "$selection" ]] && return
  cd "$selection" || return
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
