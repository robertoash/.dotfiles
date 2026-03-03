#!/usr/bin/env bash
# Hyprland session wrapper - called by greetd instead of start-hyprland directly.
# Ensures secrets and systemd user env are available BEFORE Hyprland starts,
# so all keybind-launched processes inherit them automatically.

set -euo pipefail

secrets_dir="${XDG_RUNTIME_DIR:-/run/user/$UID}/secrets"

# Decrypt secrets directly (faster than waiting for systemd service ordering).
# This also sets the systemd user env so services that start later get them too.
"$HOME/.dotfiles/common/scripts/decrypt-secrets.sh"

# Load secrets into our process env so Hyprland inherits them
if [[ -d "$secrets_dir" ]]; then
    for f in "$secrets_dir"/*; do
        [[ -f "$f" ]] || continue
        name=$(basename "$f")
        [[ "$name" == .* ]] && continue
        var=$(echo "$name" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
        export "$var=$(cat "$f")"
    done
fi

# Import global vars from systemd user environment (EDITOR, BROWSER, etc.)
while IFS= read -r line; do
    # Skip empty lines and read-only vars
    case "${line%%=*}" in
        ""|PATH|HOME|USER|LOGNAME|SHELL|TERM|SHLVL|PWD|_) continue ;;
    esac
    export "$line"
done < <(systemctl --user show-environment 2>/dev/null)

exec start-hyprland "$@"
