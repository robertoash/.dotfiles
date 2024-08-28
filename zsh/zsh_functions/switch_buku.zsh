#!/bin/bash

switch_buku_db() {
    python3 "$HOME/.config/scripts/shell/switch_buku.py" "$@"
}

# Modify the startup call to use the full path
switch_buku_db "rash" --startup
