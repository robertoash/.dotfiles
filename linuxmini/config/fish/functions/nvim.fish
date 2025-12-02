function nvim
    command nvim $argv
    for f in $argv
        if test -f "$f"; and test "$SECURE_SHELL" != "1"
            fre --add "$f"
        end
    end
end