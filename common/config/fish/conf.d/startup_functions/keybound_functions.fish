# Delete until the previous slash or word boundary
function backward-kill-to-slash
  # This function would need to be implemented differently in fish
  # as zle commands don't exist in fish
  echo "backward-kill-to-slash: Not implemented for fish shell"
end

function __fzf_path_complete
  set -l cmd $BUFFER
  set -l pre ""
  set -l fuzzy ""
  set -l base ""
  set -l query ""
  set -l selected ""
  set -l new_path ""

  # Split the command into words and get the last one
  set -l words (string split ' ' $cmd)
  set -l last_word $words[-1]

  # Only proceed if the last word contains a slash
  if string match -q "*/*" $last_word
    set pre (string replace -r "$last_word\$" "" $cmd)
    set fuzzy $last_word
  else
    set pre ""
    set fuzzy $cmd
  end

  # Get the dirname
  set base (dirname $fuzzy)

  # Handle any path that starts with ~
  if string match -q "~*" $base
    set base (string replace "~" $HOME $base)
  end

  # Remove any wildcards or special characters from the query
  set query (basename $fuzzy)
  set query (string replace -a '*' '' $query)
  set query (string replace -a '?' '' $query)
  set query (string replace -a '[' '' $query)
  set query (string replace -a ']' '' $query)

  if test -d $base
    set selected (fd --type d --type f . $base | fzf --query $query)
    if test -n $selected
      # Replace $HOME with ~ for nice-looking paths
      if string match -q "$HOME*" $selected
        set new_path (string replace $HOME "~" $selected)
      else
        set new_path $selected
      end

      # In fish, we can't directly modify BUFFER like in zsh
      echo $pre$new_path
    end
  else
    echo "❌ Directory '$base' doesn't exist" >&2
  end
end