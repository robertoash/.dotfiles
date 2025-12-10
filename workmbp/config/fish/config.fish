if status is-interactive
    # Commands to run in interactive sessions can go here
end

# Disable fish greeting
set -g fish_greeting

# Add cargo bin to PATH
fish_add_path $HOME/.cargo/bin
