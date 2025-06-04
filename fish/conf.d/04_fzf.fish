# ~/.config/fish/conf.d/04_fzf.fish
# FZF Configuration

# Fzf configs
# 🧠 User-friendly wrapper configs
set -gx FZF_CONFIG_DEFAULT "fzf --preview 'bat --color=always {}' --preview-window '~3' --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff'"
set -gx FZF_CONFIG_NO_PREVIEW "fzf --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff'"
set -gx FZF_PREVIEW true

# Initialize fzf for fish if available
if command -v fzf >/dev/null 2>&1
    # fzf key bindings and fuzzy completion
    # This replaces the 'source <(fzf --zsh)' from zsh
    fzf --fish | source
end