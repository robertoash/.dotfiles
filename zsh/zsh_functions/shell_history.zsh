# Set up a trap to ensure start_history runs on shell exit
trap 'start_history' EXIT

stop_history() {
    # Store original paths
    export _HISTFILE_ORIG="${HISTFILE:-$HOME/.config/zsh/.zsh_history}"

    # Use the same directory as the original history file
    local hist_dir
    hist_dir="$(dirname "$_HISTFILE_ORIG")"

    export HISTFILE="$hist_dir/.zsh_history_tmp_$$"
    touch "$HISTFILE"

    # Stop fasd history
    export _FASD_RO="no"

    echo "Shell history stopped..."
}

start_history() {
    # Retrieve original values
    local main_histfile="${_HISTFILE_ORIG:-$HOME/.config/zsh/.zsh_history}"
    local tmp_histfile="$HISTFILE"

    # Only delete if HISTFILE is a temporary file (to avoid deleting real history)
    if [[ "$HISTFILE" != "$main_histfile" && -f "$tmp_histfile" ]]; then
        rm -f "$tmp_histfile"
    fi

    export HISTFILE="$main_histfile"  # Restore original history

    # Unset temporary variables since they are no longer needed
    unset _HISTFILE_ORIG
    unset _FASD_RO
    #unset _ZO_DATA_DIR_ORIG

    echo "Shell history started..."
}
