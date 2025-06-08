function insert_zoxide_dir --description 'FZF zoxide dir selector for Fish'
    set -l dir (zoxide query -l | fzfi)
    if test -n "$dir"
        commandline -i -- "$dir"
        commandline -f repaint
    end
end
