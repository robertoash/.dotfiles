# ~/.config/fish/conf.d/01_path.fish
# Path Configuration

# Add Cargo path
fish_add_path "$HOME/.cargo/bin"

# Add local bin path
fish_add_path "/home/rash/.local/bin"

# Add ASDF path
if test -d "$ASDF_DATA_DIR/shims"
    fish_add_path "$ASDF_DATA_DIR/shims"
end

# Add stuff to python path
set -gx PYTHONPATH "$PYTHONPATH:/home/rash/.config/scripts"

# Add nodejs to path
if command -v npm >/dev/null 2>&1
    set -gx NPM_PREFIX (npm config get prefix)
    fish_add_path "$NPM_PREFIX/bin"
end