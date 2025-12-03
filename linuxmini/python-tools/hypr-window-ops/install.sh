#!/usr/bin/env bash

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "pipx is not installed. Installing pipx..."
    pip install --user pipx
    pipx ensurepath

    # Source bashrc to update PATH
    source ~/.bashrc
fi

# Install the package in editable mode
echo "Installing hypr-window-ops with pipx using pyproject.toml configuration..."
pipx install -e .

echo "✅ Installation complete!"
echo "You can now use the hypr-window-ops command with subcommands:"
echo "  - hypr-window-ops move-windows <workspace>"
echo "  - hypr-window-ops launch-apps [--profile <profile>] [--debug]"