# --- fzf-tab tuning ---

# Git branch completion
zstyle ':completion:*:git-checkout:*' sort false

# Group support for descriptions
zstyle ':completion:*:descriptions' format '[%d]'

# Use LS_COLORS to style filenames
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}

# Preview directories using eza when completing cd
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --color=always $realpath'

# Tab UI tweaks
zstyle ':fzf-tab:*' fzf-command ftb-tmux-popup
zstyle ':fzf-tab:*' switch-group '<' '>'
zstyle ':fzf-tab:*' prefix ''
