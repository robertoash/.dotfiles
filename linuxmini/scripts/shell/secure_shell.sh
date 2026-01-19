#!/usr/bin/env bash
# Secure, isolated Fish shell session with ephemeral history and Starship SMART_CWD

set -e

export SECURE_SHELL=1

# Temp dirs for config and data (history gets stored in data)
SECURE_XDG_CONFIG_HOME=$(mktemp -d)
FISH_CONFIG="$SECURE_XDG_CONFIG_HOME/fish"
SECURE_XDG_DATA_HOME=$(mktemp -d)
export XDG_CONFIG_HOME="$SECURE_XDG_CONFIG_HOME"
export XDG_DATA_HOME="$SECURE_XDG_DATA_HOME"

# Start nvim copy in background (not needed for shell startup)
NVIM_COPY_PID=""
if [ -d ~/.local/share/nvim ]; then
    cp -r ~/.local/share/nvim "$SECURE_XDG_DATA_HOME/nvim" &
    NVIM_COPY_PID=$!
fi

# Copy fish config synchronously - needed for proper shell startup with starship/completions/etc
cp -r ~/.config/fish "$FISH_CONFIG"

# Copy yazi config so custom keybindings (like !) work in secure shell
if [ -d ~/.config/yazi ]; then
    cp -r ~/.config/yazi "$SECURE_XDG_CONFIG_HOME/yazi"
fi

# Ensure all config files are fully written to disk
sync

# Valid history session name (letters/numbers/underscores only)
SESSION_ID="secure_shell_$(date +%s)_$RANDOM"

# Inject secure config into conf.d (history & SMART_CWD) - AFTER copy completes
cat > "$FISH_CONFIG/conf.d/99-secure-shell.fish" <<EOF
# Secure shell: Ephemeral Fish history and Starship SMART_CWD

set -gx fish_history $SESSION_ID

set -gx SECURE_SHELL 1
EOF

# Link buku database directory to real location
ln -s ~/.local/share/buku "$SECURE_XDG_DATA_HOME/buku"

cleanup() {
    # Switch back to rash if we're on rashp (encrypts using password from db)
    python3 ~/.config/scripts/shell/switch_buku.py rash 2>/dev/null || true
    
    # Clean up all temp dirs/files, including ephemeral fish history
    rm -rf "$SECURE_XDG_CONFIG_HOME"
    rm -rf "$SECURE_XDG_DATA_HOME"
}
trap cleanup EXIT HUP INT QUIT TERM

fish
