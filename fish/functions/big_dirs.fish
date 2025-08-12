function big_dirs --description 'List directories recursively sorted by size with fzf'
    dust -d 999 -p -b -P -X .git -r -D | \
    fzf --height=12 \
        --layout=reverse \
        --border \
        --ansi \
        --no-sort \
        --tiebreak=index \
        --header='Dirs by size (Enter: open, Ctrl-D: delete, Esc: quit)' \
        --prompt='Size ranked > ' \
        --bind='ctrl-d:execute-silent(echo {} | awk "{print \$NF}" | xargs -r rm -rf)+reload(dust -d 999 -p -b -P -X .git -r -D)'
end