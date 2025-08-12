function big_files --description 'List files recursively sorted by size with fzf'
    dust -d 999 -p -b -P -X .git -r -F | \
    fzf --height=12 \
        --layout=reverse \
        --border \
        --ansi \
        --no-sort \
        --tiebreak=index \
        --header='Files by size (Enter: open, Ctrl-D: delete, Esc: quit)' \
        --prompt='Size ranked > ' \
        --bind='ctrl-d:execute-silent(echo {} | awk "{print \$NF}" | xargs -r rm -f)+reload(dust -d 999 -p -b -P -X .git -r -F)'
end