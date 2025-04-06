
## Navigation
bindkey '^a' beginning-of-line
bindkey '^e' end-of-line
bindkey "^[[3~" delete-char
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down

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

## Keybinds set by fzf
# source <(fzf --zsh) in .zshrc
# CTRL+T -> Fuzzy file search
# CTRL+R -> Fuzzy history search
# ALT+C -> Fuzzy cd
