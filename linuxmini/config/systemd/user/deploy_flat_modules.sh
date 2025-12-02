#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$HOME/.config/systemd/user"
TARGET_DIR="/etc/systemd/user"

echo "🔍 Searching for units inside subfolders of $SOURCE_DIR..."
echo "🚫 Skipping files in the top-level directory."

mapfile -t units < <(
  find "$SOURCE_DIR" -mindepth 2 -type f \( -name "*.service" -o -name "*.timer" -o -name "*.path" \)
)

for src in "${units[@]}"; do
    base="$(basename "$src")"
    dest="$TARGET_DIR/$base"

    if [[ -e "$dest" ]]; then
        echo "🟡 Found existing $base, backing up → $base.bkup"
        sudo mv "$dest" "$dest.bkup"
    fi

    echo "✅ Installing $base → $TARGET_DIR"
    sudo install -m 644 "$src" "$dest"
done

echo "🔁 Reloading user systemd daemon..."
systemctl --user daemon-reexec
