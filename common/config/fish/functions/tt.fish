# Defined interactively
function tt --description 'File selector using fd'
    if test (count $argv) -eq 0
        fd -Hi -t f | fzf
    else
        # Filter fd files by the provided search term
        fd -Hi -t f 2>/dev/null | grep -i (string join '.*' $argv)
    end
end
