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
            dust -d 999 -p -b -P -X .git -r -D | \
            fzf --height=12 \
                --layout=reverse \
                --border \
                --ansi \
                --no-sort \
                --tiebreak=index \
                --header='Dirs by size (Enter: open, Ctrl-D: delete, Esc: quit)' \
                --prompt='Size ranked > ' \
                --bind='ctrl-d:execute-silent(echo {} | awk "{print \$NF}" | xargs -r trash put)+reload(dust -d 999 -p -b -P -X .git -r -D)' \
                --bind='enter:execute(echo {} | awk "{print \$NF}" | xargs -r yazi)'
                
        case files
            dust -d 999 -p -b -P -X .git -r -F | \
            fzf --height=12 \
                --layout=reverse \
                --border \
                --ansi \
                --no-sort \
                --tiebreak=index \
                --header='Files by size (Enter: open, Ctrl-D: delete, Esc: quit)' \
                --prompt='Size ranked > ' \
                --bind='ctrl-d:execute-silent(echo {} | awk "{print \$NF}" | xargs -r trash put)+reload(dust -d 999 -p -b -P -X .git -r -F)' \
                --bind='enter:execute-silent(echo {} | awk "{print \$NF}" | xargs -r xdg-open)'
                
        case all
            dust -d 999 -p -b -P -X .git -r | \
            fzf --height=12 \
                --layout=reverse \
                --border \
                --ansi \
                --no-sort \
                --tiebreak=index \
                --header='All items by size (Enter: open, Ctrl-D: delete, Esc: quit)' \
                --prompt='Size ranked > ' \
                --bind='ctrl-d:execute-silent(echo {} | awk "{print \$NF}" | xargs -r trash put)+reload(dust -d 999 -p -b -P -X .git -r)' \
                --bind='enter:execute(echo {} | awk "{print \$NF}" | xargs -r -I {} sh -c "test -d \"{}\" && yazi \"{}\" || xdg-open \"{}\"")'
    end
end