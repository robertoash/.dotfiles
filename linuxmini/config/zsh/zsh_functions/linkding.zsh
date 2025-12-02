open_in_vivaldi_rash() {
    url="$1"
    vivaldi --profile-directory="rash" --new-tab "$url"
}

lkd() {
  if [[ -n "$1" ]]; then
    url=$(linkding bookmarks all --query "$1" | jq -r '.results[0].url')
    [[ -n "$url" ]] && open_in_vivaldi_rash "$url" || echo "❌ No bookmark found for: $1"
  else
    tmpfile=$(mktemp)
    linkding bookmarks all | jq -c '.results[] | {title: (.title // "(no title)"), data: .}' > "$tmpfile"

    selected=$(jq -r '.title' "$tmpfile" | \
      fzf \
        --prompt="Linkding   " \
        --preview="cat \"$tmpfile\" | jq --color-output -r --arg title {} 'select(.title == \$title) | .data'" \
        --preview-window=right:50% \
        --header="Select a bookmark to open")

    if [[ -n "$selected" ]]; then
      url=$(cat "$tmpfile" | jq -r --arg title "$selected" 'select(.title == $title) | .data.url')
      open_in_vivaldi_rash "$url"
    fi

    rm -f "$tmpfile"
  fi
}

