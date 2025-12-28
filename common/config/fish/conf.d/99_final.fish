# ~/.config/fish/conf.d/99_final.fish
# Final Setup and Prompt Configuration

# Load Starship prompt
if command -v starship >/dev/null 2>&1
    starship init fish | source
end

# Initialize smart cwd on startup
__smart_cwd_hook

# Show welcome banner with image (fast chafa instead of slow fastfetch)
if status is-interactive && not set -q YAZI_LEVEL
    welcome-banner
end

