function lkd
  if test -n "$argv[1]"
    set url (linkding bookmarks all --query $argv[1] | jq -r '.results[0].url')
    test -n "$url" && open_in_browser_rash $url || echo "❌ No bookmark found for: $argv[1]"
  else
    set tmpfile (mktemp)
    linkding bookmarks all | jq -c '.results[] | {title: (.title // "(no title)"), data: .}' > $tmpfile

    set selected (jq -r '.title' $tmpfile | \
      fzf \
        --prompt="Linkding   " \
        --preview="cat \"$tmpfile\" | jq --color-output -r --arg title {} 'select(.title == \$title) | .data'" \
        --preview-window=right:50% \
        --header="Select a bookmark to open")

    if test -n "$selected"
      set url (cat $tmpfile | jq -r --arg title $selected 'select(.title == $title) | .data.url')
      open_in_browser_rash $url
    end

    rm -f $tmpfile
  end
end

