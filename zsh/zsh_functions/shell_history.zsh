# Set up traps to ensure cleanup on any exit
trap 'start_history' EXIT
trap 'start_history' HUP
trap 'start_history' INT
trap 'start_history' QUIT
trap 'start_history' TERM

stop_history() {
    # If history is already stopped (we have a temporary file), ignore the call
    if [[ -n "$_HISTFILE_ORIG" ]]; then
        echo "History already stopped"
        return 0
    fi

    # Store original paths
    export _HISTFILE_ORIG="${HISTFILE:-$HOME/.config/zsh/.zsh_history}"

    # Use the same directory as the original history file
    local hist_dir
    hist_dir="$(dirname "$_HISTFILE_ORIG")"

    # Create a unique temporary history file for this terminal
    export HISTFILE="$hist_dir/.zsh_history_tmp_${PPID}_$$"
    touch "$HISTFILE"

    # Stop fasd history
    export _FASD_RO="no"

    echo "Shell history stopped..."
}

start_history() {
    # If history is already started (no temporary file), ignore the call
    if [[ -z "$_HISTFILE_ORIG" ]]; then
        echo "History already started"
        return 0
    fi

    # Retrieve original values
    local main_histfile="${_HISTFILE_ORIG:-$HOME/.config/zsh/.zsh_history}"
    local tmp_histfile="$HISTFILE"

    # Clean up this terminal's temporary history file
    if [[ -n "$tmp_histfile" && "$tmp_histfile" != "$main_histfile" ]]; then
        rm -f "$tmp_histfile" 2>/dev/null
    fi

    export HISTFILE="$main_histfile"  # Restore original history

    # Clear the in-memory history and reload from main history file
    fc -P
    fc -p "$main_histfile"

    # Unset temporary variables since they are no longer needed
    unset _HISTFILE_ORIG
    unset _FASD_RO
    #unset _ZO_DATA_DIR_ORIG

    echo "Shell history started..."
}
