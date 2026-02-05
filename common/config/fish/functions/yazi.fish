# Use y to change cwd on yazi exit
function yazi
    set tmp (mktemp -t "yazi-cwd.XXXXXX")
    command yazi $argv --cwd-file="$tmp"
    if set cwd (cat -- "$tmp") && test -n "$cwd" && test "$cwd" != "$PWD"
        builtin cd -- "$cwd"
    end
    command rm -f -- "$tmp"
end