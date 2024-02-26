#!/bin/bash

# Save the current working directory
CWD=$(pwd)

# Define the location of your patch file
PATCH_FILE="/home/rash/.config/yay/patches/nomacs.patch"

# Create a temporary directory
TEMP_DIR="/tmp/nomacs"
mkdir -p "$TEMP_DIR"

# Change to the temporary directory
cd "$TEMP_DIR"

# Fetch the latest PKGBUILD with yay
yay -G nomacs-git

# Change to the directory where yay cloned the PKGBUILD
cd nomacs-git

# Apply the patch to the PKGBUILD
patch PKGBUILD < "$PATCH_FILE"

# Build and install the package
makepkg -si

# Cleanup: Return to the original working directory and remove the temp directory
cd "$CWD"
rm -rf "$TEMP_DIR"
