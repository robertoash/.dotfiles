function fzfn
    set -gx FZF_PREVIEW false
    command fzf $argv
end
