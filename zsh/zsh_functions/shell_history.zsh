# Set up a trap to ensure start_history runs on shell exit
trap 'start_history' EXIT

stop_history() {
    # Store original paths
    export _HISTFILE_ORIG="${HISTFILE:-$HOME/.config/zsh/.zsh_history}"
    export _ZO_DATA_DIR_ORIG="${_ZO_DATA_DIR:-$HOME/.config/zoxide}"

    # Use the same directory as the original history file
    local hist_dir
    hist_dir="$(dirname "$_HISTFILE_ORIG")"

    export HISTFILE="$hist_dir/.zsh_history_tmp_$$"
    touch "$HISTFILE"

    # Create a temp dir under the original zoxide directory
    export _ZO_DATA_DIR="$_ZO_DATA_DIR_ORIG/temp/"
    mkdir -p "$_ZO_DATA_DIR"  # Ensure temp dir exists

    echo "Shell history stopped..."
}

start_history() {
    # Retrieve original values
    local main_histfile="${_HISTFILE_ORIG:-$HOME/.config/zsh/.zsh_history}"
    local original_zoxide_dir="${_ZO_DATA_DIR_ORIG:-$HOME/.config/zoxide}"
    local tmp_histfile="$HISTFILE"

    # Only delete if HISTFILE is a temporary file (to avoid deleting real history)
    if [[ "$HISTFILE" != "$main_histfile" && -f "$tmp_histfile" ]]; then
        rm -f "$tmp_histfile"
    fi

    export HISTFILE="$main_histfile"  # Restore original history
    export _ZO_DATA_DIR="$original_zoxide_dir"  # Restore zoxide data directory

    rm -rf "$original_zoxide_dir/temp/"  # Clean up temp directory

    # Unset temporary variables since they are no longer needed
    unset _HISTFILE_ORIG
    unset _ZO_DATA_DIR_ORIG
    
    echo "Shell history started..."
}
