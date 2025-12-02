function nvim
    command nvim $argv
    for f in $argv
        if test -f "$f"; and test "$SECURE_SHELL" != "1"
            # Convert to absolute path before adding to fre
            set -l abs_path (realpath "$f" 2>/dev/null)
            if test -n "$abs_path"
                fre --add "$abs_path"
            end
        end
    end
end