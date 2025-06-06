# ~/.config/fish/conf.d/99_final.fish
# Final Setup and Prompt Configuration

# Load Starship prompt
if command -v starship >/dev/null 2>&1
    starship init fish | source
end

# Launch neofetch only in interactive shells and not within yazi
if status is-interactive && not set -q YAZI_LEVEL
    clear && fastfetch
end
