
## Navigation
bindkey '^a' beginning-of-line
bindkey '^e' end-of-line
bindkey "^[[3~" delete-char
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down
bindkey '^R' fzf_history_widget

# Fasd completion widgets
bindkey '^X^A' fasd-complete    # C-x C-a to do fasd-complete (files and directories)
bindkey '^X^F' fasd-complete-f  # C-x C-f to do fasd-complete-f (only files)
bindkey '^X^D' fasd-complete-d  # C-x C-d to do fasd-complete-d (only directories)

# Alt + LeftArrow -> backward-word
bindkey "^[[1;3D" backward-word
# Alt + RightArrow -> forward-word
bindkey "^[[1;3C" forward-word


if (( ${+terminfo[smkx]} )) && (( ${+terminfo[rmkx]} )); then
  function zle-line-init() {
    echoti smkx
  }
  function zle-line-finish() {
    echoti rmkx
  }
  zle -N zle-line-init
  zle -N zle-line-finish
fi


## Live history suggestions below the prompt
autoload -U up-line-or-beginning-search
autoload -U down-line-or-beginning-search

fzf_history_widget() {
    disable_fzf_preview
    local selected
    selected=$(history -n 1 | tac | awk '!seen[$0]++' | fzf --height=40 --reverse --no-sort --border --color='fg:#cdd6f4,fg+:#cdd6f4,bg:#1e1e2e,preview-bg:#1e1e2e,border:#89b4fa' --query "$LBUFFER")
    if [[ -n $selected ]]; then
        LBUFFER=$selected
    fi
    zle reset-prompt
    restore_fzf_preview
}

## Bind fzf-powered history search to arrow keys
zle -N fzf_history_widget

# [Home] - Go to beginning of line
if [[ -n "${terminfo[khome]}" ]]; then
  bindkey -M emacs "${terminfo[khome]}" beginning-of-line
  bindkey -M viins "${terminfo[khome]}" beginning-of-line
  bindkey -M vicmd "${terminfo[khome]}" beginning-of-line
fi
# [End] - Go to end of line
if [[ -n "${terminfo[kend]}" ]]; then
  bindkey -M emacs "${terminfo[kend]}"  end-of-line
  bindkey -M viins "${terminfo[kend]}"  end-of-line
  bindkey -M vicmd "${terminfo[kend]}"  end-of-line
fi
