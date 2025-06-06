function fzfp
    set -gx FZF_PREVIEW true
    command fzf $argv
end
