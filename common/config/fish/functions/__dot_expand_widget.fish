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

    # Create a state file to track current directory level
    set -l state_file /tmp/dot-expand-state-$fish_pid
    echo "$search_dir" > $state_file

    # Create a reload script that lists directories and updates state
    set -l reload_cmd "bash -c 'dir=\$(cat $state_file 2>/dev/null || echo \"$search_dir\"); parent=\$(dirname \"\$dir\"); if [ \"\$parent\" != \"\$dir\" ]; then echo \"\$parent\" > $state_file; command ls -1Adp \"\$parent\"/*/ \"\$parent\"/.*/ 2>/dev/null | grep -v \"/\\.\$\" | grep -v \"/\\.\\.\$\" | sed \"s|/\$||\"; else command ls -1Adp \"\$dir\"/*/ \"\$dir\"/.*/ 2>/dev/null | grep -v \"/\\.\$\" | grep -v \"/\\.\\.\$\" | sed \"s|/\$||\"; fi'"

    # Initial directory listing using native globbing (includes hidden dirs)
    set -l result (command ls -1Adp "$search_dir"/*/ "$search_dir"/.*/ 2>/dev/null | \
        grep -v '/\.$' | grep -v '/\.\.$' | sed 's|/$||' | \
        fzf --height 40% --reverse \
            --header "Press . to go up, Enter to select, Esc to keep current path" \
            --bind ".:reload($reload_cmd)+change-header(Going up...)" \
            --query "")

    # Read final directory level from state file
    set -l final_dir (cat $state_file 2>/dev/null)
    command rm -f $state_file

    if test -n "$result"
        # User selected something
        commandline -t -- "$result/"
        set -e __dot_expand_level
        commandline -f repaint
    else if test -n "$final_dir"; and test "$final_dir" != "$search_dir"
        # User cancelled but navigated up - keep the ancestor path
        commandline -t -- "$final_dir/"
        commandline -f repaint
    else
        # User cancelled at same level - keep current path
        commandline -f repaint
    end
end
