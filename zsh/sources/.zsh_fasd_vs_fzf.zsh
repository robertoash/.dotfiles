# ~/.config/zsh/.zsh_fasd_vs_fzf.zsh

# Only override Tab behavior; leave default completion untouched
# Fasd will still inject its _fasd_zsh_word_complete_trigger as a fallback via zstyle

# Decide if the current word looks like a fasd word-mode trigger
_fzf_should_ignore_for_fasd() {
  local word="${words[CURRENT]}"
  [[ "$word" == f,* || "$word" == d,* || "$word" == ,* || "$word" == *, || "$word" == *,f || "$word" == *,d ]]
}

# Smart Tab override: delegate based on fasd-style trigger
fzf_fasd_smart_tab() {
  if _fzf_should_ignore_for_fasd; then
    # fallback to builtin Tab so fasd completions can hook in properly
    zle ${fzf_default_completion:-expand-or-complete}
  else
    zle fzf-completion
  fi
}
zle -N fzf_fasd_smart_tab
bindkey '^I' fzf_fasd_smart_tab
