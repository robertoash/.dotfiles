# Widget function bound to '.' key for live multi-dot expansion
# Typing ... expands to grandparent path, each additional . goes up one more level
function __dot_expand_widget
    set -l token (commandline -t)
    set -l cmd (commandline -b)

    # Case 1: Token is ".." - third dot triggers expansion
    if test "$token" = ".."
        # Calculate grandparent (2 levels up)
        set -l target (dirname (dirname $PWD))
        if test "$target" != "/"
            commandline -t -- "$target"
            # Store the level we're at for subsequent dots
            set -g __dot_expand_level 2
        else
            commandline -t -- "/"
            set -g __dot_expand_level 999
        end
        return
    end

    # Case 2: Token is an already-expanded ancestor path - go up one more level
    if set -q __dot_expand_level; and test -d "$token"
        set -l target (dirname $token)
        # Only expand if we're not at root
        if test "$target" != "$token"
            set -g __dot_expand_level (math $__dot_expand_level + 1)
            commandline -t -- "$target"
            return
        end
    end

    # Case 3: Normal dot - just insert it
    commandline -i '.'
    # Clear expansion state since we're typing something else
    set -e __dot_expand_level
end
