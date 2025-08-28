# ~/.config/fish/conf.d/99_final.fish
# Final Setup and Prompt Configuration

# Load Starship prompt
if command -v starship >/dev/null 2>&1
    starship init fish | source
end

# Launch neofetch only in interactive shells and not within yazi
if status is-interactive && not set -q YAZI_LEVEL
    command fastfetch
end

# Auto-switch back to rash database on shell exit to ensure rashp is encrypted
function __buku_exit_handler --on-event fish_exit
    # Only run if not in secure shell (secure shell has its own handler)
    if not set -q SECURE_SHELL
        python3 ~/.config/scripts/shell/switch_buku.py rash 2>/dev/null
    end
end
