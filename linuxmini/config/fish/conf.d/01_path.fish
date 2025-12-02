# ~/.config/fish/conf.d/01_path.fish
# Path Configuration

# Add Cargo pkgs to path
fish_add_path "$HOME/.cargo/bin"

# Add Go pkgs to path
fish_add_path (go env GOPATH)/bin

# Add local bin path
fish_add_path "/home/rash/.local/bin"

# Add stuff to python path
set -gx PYTHONPATH "$PYTHONPATH:/home/rash/.config/scripts"
