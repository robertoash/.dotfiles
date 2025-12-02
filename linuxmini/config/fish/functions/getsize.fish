function getsize --description 'List files/directories recursively sorted by size with fzf'
    set -l mode "dirs"
    
    for arg in $argv
        switch $arg
            case -d --dirs
                set mode "dirs"
            case -f --files
                set mode "files"
            case -a --all
                set mode "all"
            case -h --help
                echo "Usage: getsize [OPTIONS]"
                echo "Options:"
                echo "  -d, --dirs   List directories only (default)"
                echo "  -f, --files  List files only"
                echo "  -a, --all    List both files and directories"
                echo "  -h, --help   Show this help message"
                return 0
            case '*'
                echo "Unknown option: $arg"
                echo "Use 'getsize --help' for usage information"
                return 1
        end
    end
    
    switch $mode
        case dirs
            dust -d 999 -X .git -r -D -j | jq -r '.children[] | select(.children | length > 0) | "\(.size) \(.name)"' | \
            fzf --height=12 \
                --layout=reverse \
                --border \
                --no-sort \
                --tiebreak=index \
                --header='Dirs by size (Enter: open, Alt-D: delete, Alt-C: copy path, Esc: quit)' \
                --prompt='Size ranked > ' \
                --bind='alt-d:execute-silent(echo {} | awk "{for(i=2;i<=NF;i++) printf \"%s%s\", \$i, (i<NF?\" \":\"\")}" | xargs -r -d '"'"'\n'"'"' trash-put)+reload(dust -d 999 -X .git -r -D -j | jq -r '"'"'.children[] | select(.children | length > 0) | "\(.size) \(.name)"'"'"')' \
                --bind='alt-c:execute-silent(echo {} | awk "{for(i=2;i<=NF;i++) printf \"%s%s\", \$i, (i<NF?\" \":\"\")}" | wl-copy)' \
                --bind='enter:execute(echo {} | awk "{for(i=2;i<=NF;i++) printf \"%s%s\", \$i, (i<NF?\" \":\"\")}" | xargs -r -d '"'"'\n'"'"' yazi)'
                
        case files
            dust -d 999 -X .git -r -F -j | jq -r '.children[] | "\(.size) \(.name)"' | \
            fzf --height=12 \
                --layout=reverse \
                --border \
                --no-sort \
                --tiebreak=index \
                --header='Files by size (Enter: open, Alt-D: delete, Alt-C: copy path, Esc: quit)' \
                --prompt='Size ranked > ' \
                --bind='alt-d:execute-silent(echo {} | awk "{for(i=2;i<=NF;i++) printf \"%s%s\", \$i, (i<NF?\" \":\"\")}" | xargs -r -d '"'"'\n'"'"' trash-put)+reload(dust -d 999 -X .git -r -F -j | jq -r '"'"'.children[] | "\(.size) \(.name)"'"'"')' \
                --bind='alt-c:execute-silent(echo {} | awk "{for(i=2;i<=NF;i++) printf \"%s%s\", \$i, (i<NF?\" \":\"\")}" | wl-copy)' \
                --bind='enter:execute-silent(echo {} | awk "{for(i=2;i<=NF;i++) printf \"%s%s\", \$i, (i<NF?\" \":\"\")}" | xargs -r -d '"'"'\n'"'"' xdg-open)'
                
        case all
            dust -d 999 -X .git -r -j | jq -r '.children[] | "\(.size) \(.name)"' | \
            fzf --height=12 \
                --layout=reverse \
                --border \
                --no-sort \
                --tiebreak=index \
                --header='All items by size (Enter: open, Alt-D: delete, Alt-C: copy path, Esc: quit)' \
                --prompt='Size ranked > ' \
                --bind='alt-d:execute-silent(echo {} | awk "{for(i=2;i<=NF;i++) printf \"%s%s\", \$i, (i<NF?\" \":\"\")}" | xargs -r -d '"'"'\n'"'"' trash-put)+reload(dust -d 999 -X .git -r -j | jq -r '"'"'.children[] | "\(.size) \(.name)"'"'"')' \
                --bind='alt-c:execute-silent(echo {} | awk "{for(i=2;i<=NF;i++) printf \"%s%s\", \$i, (i<NF?\" \":\"\")}" | wl-copy)' \
                --bind='enter:execute(echo {} | awk "{for(i=2;i<=NF;i++) printf \"%s%s\", \$i, (i<NF?\" \":\"\")}" | xargs -r -d '"'"'\n'"'"' -I {} sh -c "test -d \"{}\" && yazi \"{}\" || xdg-open \"{}\"")'
    end
end