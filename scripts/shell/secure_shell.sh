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

# Start copy operations in background
cp -r ~/.config/fish "$FISH_CONFIG" &
FISH_COPY_PID=$!

NVIM_COPY_PID=""
if [ -d ~/.local/share/nvim ]; then
    cp -r ~/.local/share/nvim "$SECURE_XDG_DATA_HOME/nvim" &
    NVIM_COPY_PID=$!
fi

# Valid history session name (letters/numbers/underscores only)
SESSION_ID="secure_shell_$(date +%s)_$RANDOM"

# Inject secure config into conf.d (history & SMART_CWD)
mkdir -p "$FISH_CONFIG/conf.d"
cat > "$FISH_CONFIG/conf.d/99-secure-shell.fish" <<EOF
# Secure shell: Ephemeral Fish history and Starship SMART_CWD

set -gx fish_history $SESSION_ID

set -gx SECURE_SHELL 1
EOF

# Wait for fish copy to complete (needed for shell startup)
wait $FISH_COPY_PID

cleanup() {
    # Clean up all temp dirs/files, including ephemeral fish history
    rm -rf "$SECURE_XDG_CONFIG_HOME"
    rm -rf "$SECURE_XDG_DATA_HOME"
}
trap cleanup EXIT HUP INT QUIT TERM

fish
