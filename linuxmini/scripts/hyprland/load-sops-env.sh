#!/usr/bin/env bash
# Inject sops secrets into Hyprland's environment via hyprctl keyword env.
# Run as exec-once so all keybind-launched processes inherit the secrets.
# Must run before dbus-update-activation-environment to propagate to D-Bus/systemd too.

secrets_dir="${XDG_RUNTIME_DIR:-/run/user/$UID}/secrets"

[[ -d "$secrets_dir" ]] || exit 0

for secret_file in "$secrets_dir"/*; do
    [[ -f "$secret_file" ]] || continue
    name=$(basename "$secret_file")
    [[ "$name" == .* ]] && continue
    env_var=$(echo "$name" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
    hyprctl keyword env "$env_var,$(cat "$secret_file")" --quiet
done
