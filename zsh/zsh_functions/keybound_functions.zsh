# Delete until the previous slash or word boundary
backward-kill-to-slash() {
  local WORDCHARS_BACKUP=$WORDCHARS
  # To treat all punctuation (like /) as delimiters: WORDCHARS=''
  WORDCHARS="${WORDCHARS:s:/:}"
  zle backward-kill-word
  WORDCHARS=$WORDCHARS_BACKUP
}
zle -N backward-kill-to-slash

function __fzf_path_complete() {
  local cmd=$BUFFER
  local pre fuzzy base query selected new_path

  # Split the command into words and get the last one
  local words=(${(z)cmd})
  local last_word=${words[-1]}

  # Only proceed if the last word contains a slash
  if [[ "$last_word" == */* ]]; then
    pre=${cmd%$last_word}
    fuzzy=$last_word
  else
    pre=""
    fuzzy=$cmd
  fi

  # Expand ~ manually and get the dirname
  base="${fuzzy:h}"
  base="${~base}"  # this is key: expands ~, variables, etc.

  # Handle any path that starts with ~
  if [[ "$base" == "~"* ]]; then
    base="${base/#\~/$HOME}"
  fi

  # Remove any wildcards or special characters from the query
  query="${fuzzy##*/}"
  query="${query//[\*\?\[\]]/}"

  if [[ -d "$base" ]]; then
    selected=$(fd --type d --type f . "$base" | fzf --query "$query")
    if [[ -n "$selected" ]]; then
      # Replace $HOME with ~ for nice-looking paths
      if [[ "$selected" == "$HOME"* ]]; then
        new_path="~${selected#$HOME}"
      else
        new_path="$selected"
      fi

      BUFFER="${pre}${new_path}"
      CURSOR=${#BUFFER}
    fi
  else
    zle -M "❌ Directory '$base' doesn't exist"
  fi
}
zle -N __fzf_path_complete