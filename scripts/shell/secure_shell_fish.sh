#!/usr/bin/env bash
# Secure, isolated Fish shell session with ephemeral history and Starship SMART_CWD

set -e

export SECURE_SHELL=1

# Temp dirs for config and data (history gets stored in data)
FISH_CONFIG_PARENT=$(mktemp -d)
FISH_CONFIG="$FISH_CONFIG_PARENT/fish"
cp -r ~/.config/fish "$FISH_CONFIG"

FISH_DATA_PARENT=$(mktemp -d)
export XDG_CONFIG_HOME="$FISH_CONFIG_PARENT"
export XDG_DATA_HOME="$FISH_DATA_PARENT"

# Valid history session name (letters/numbers/underscores only)
SESSION_ID="secure_shell_$(date +%s)_$RANDOM"

# Inject secure config into conf.d (history & SMART_CWD)
mkdir -p "$FISH_CONFIG/conf.d"
cat > "$FISH_CONFIG/conf.d/99-secure-shell.fish" <<EOF
# Secure shell: Ephemeral Fish history and Starship SMART_CWD

set -gx fish_history $SESSION_ID

set -gx SECURE_SHELL 1
EOF

cleanup() {
    # Clean up all temp dirs/files, including ephemeral fish history
    rm -rf "$FISH_CONFIG_PARENT"
    rm -rf "$FISH_DATA_PARENT"
}
trap cleanup EXIT HUP INT QUIT TERM

fish
