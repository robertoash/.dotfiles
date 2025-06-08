function insert_fre_file --description 'FZF fre file selector for Fish'
    set -l file (fre --sorted | tail -n +1 | fzfi)
    if test -n "$file"
        # Get only the last line (the actual file selection), ignoring any query input
        set -l selection (echo "$file" | tail -n 1)
        if test -n "$selection"
            commandline -i -- "$selection"
            commandline -f repaint
        end
    end
end
