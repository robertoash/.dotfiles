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
            commandline -t -- "$target/"
            # Store the level we're at for subsequent dots
            set -g __dot_expand_level 2
            # Launch fzf for directory selection
            __dot_expand_fzf "$target" 2
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
            commandline -t -- "$target/"
            # Launch fzf for directory selection
            __dot_expand_fzf "$target" $__dot_expand_level
            return
        end
    end

    # Case 3: Normal dot - just insert it
    commandline -i '.'
    # Clear expansion state since we're typing something else
    set -e __dot_expand_level
end

# Helper function to launch fzf with special '.' handling
function __dot_expand_fzf
    set -l search_dir $argv[1]
    set -l level $argv[2]

    # Create a marker file for detecting '.' press
    set -l marker /tmp/dot-expand-marker-$fish_pid
    command rm -f $marker

    # Launch fzf with special binding for '.' to continue expansion
    set -l result (fd -Hi --no-ignore-vcs -t d --max-depth 1 . "$search_dir" 2>/dev/null | \
        fzf --height 40% --reverse \
            --bind ".:execute-silent(touch $marker)+abort" \
            --query "")

    if test -f "$marker"
        # User pressed '.', go up one more level
        command rm -f $marker
        set -l target (dirname "$search_dir")
        if test "$target" != "$search_dir"
            set -g __dot_expand_level (math $level + 1)
            commandline -t -- "$target/"
            # Recursively launch fzf for the next level
            __dot_expand_fzf "$target" $__dot_expand_level
        end
    else if test -n "$result"
        # User selected something
        commandline -t -- "$result/"
        set -e __dot_expand_level
        commandline -f repaint
    else
        # User cancelled (Esc or Ctrl+C) - keep current path
        commandline -f repaint
    end
end
