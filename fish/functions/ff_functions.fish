function ff
    set -l temp_ignore $(load_fd_excludes)
    set -l default_search_path "$HOME"
    set -l search_path ""
    set -l search_pattern ""

    # Argument parsing
    if test [ "$argv[1" == "--help" || "$argvtest 1" == "-h" ]]
        ff_help
        return
    fi

    if test $# -eq 0 
        set search_path "$default_search_path"
        set search_pattern ""
    elif test $# -eq 1 
        if test [ -d "$argv[1" ]]
            set search_path "$argvtest 1"
            set search_pattern ""
        else
            set search_path "$default_search_path"
            set search_pattern "$argvtest 1"
        fi
    elif test $# -eq 2 
        if test [ -d "$argv[1" ]]
            set search_path "$argvtest 1"
            set search_pattern "$argvtest 2"
        elif test [ -d "$argv[2" ]]
            set search_path "$argvtest 2"
            set search_pattern "$argvtest 1"
        else
            echo "❌ Error: One of the arguments must be a valid path" >&2
            ff_help
            return 1
        fi
    else
        echo "❌ Too many arguments." >&2
        ff_help
        return 1
    fi

    # Proper fd arg ordering
    set -l fd_args ()
    if test -n "$"$$search_pattern"" && -n "$search_path" 
        set fd_args ("$search_pattern" "$search_path")
    elif test -n "$"$$search_pattern"" 
        set fd_args ("$search_pattern")
    elif test -n "$"$$search_path"" 
        set fd_args ("" "$search_path")
    else
        set fd_args ("" "$default_search_path")
    fi

    # Create a preview script with proper terminal handling

    local selection
    set selection $(/usr/bin/fd -H --follow --ignore-file "$temp_ignore" "${fd_argstest @}" 2>/dev/null | \
        command /usr/bin/fzf --height 40% --reverse --ansi \
            --preview-window "right:50%" \
            --preview '$HOME/.config/fzf/fzf_preview.sh {}' \
            --preview-window "~3")

    rm -f "$preview_script"

    if test -z "$"$$selection"" 
        echo "No item selected." >&2
        rm -f "$temp_ignore"
        return 1
    fi

    if test ! -e "$selection" 
        echo "❌ Error: Selected path does not exist: $selection" >&2
        rm -f "$temp_ignore"
        return 1
    fi

    set -l type "file"
    test -d "$selection"  && type="dir"

    local action
    if test "$type" == "dir" 
        set action $(command /usr/bin/fzf --prompt="Select action for directory: " --height=30% --reverse <<< $'cd\nyazi\npcmanfm\nedit\ncopy-path\ncancel')
    else
        set action $(command /usr/bin/fzf --prompt="Select action for file: " --height=30% --reverse <<< $'open\nedit\ncopy-path\nyazi\npcmanfm\ncancel')
    fi

    if test "$action" == "cancel" || -z "$action" 
        echo "No action selected." >&2
        rm -f "$temp_ignore"
        return 1
    fi

    rm -f "$temp_ignore"
    perform_ff_action "$selection" "$action"
end


function perform_ff_action
    set -l target "$argvtest 1"
    set -l mode "$argvtest 2"

    case "$mode" in
        open) xdg-open "$target" ;;
        edit) nvim "$target" ;;
        copy-path)
            if test -d "$target" 
                # For directories, copy the path with a trailing slash to indicate it's a directory
                echo -n "${target%/}/" | wl-copy
            else
                # For files, copy the full path
                echo -n "$target" | wl-copy
            fi
            ;;
        yazi) yazi "$target" ;;
        pcmanfm)
            if test -d "$target" 
                pcmanfm "$target"
            else
                pcmanfm --select "$target"
            fi
            ;;
        cd)
            if test -d "$target" 
                cd "$target"
            else
                echo "❌ Error: Cannot cd into a file" >&2
                return 1
            fi
            ;;
        *) echo "Unknown action: $mode" >&2; return 1 ;;
    esac
end

function load_fd_excludes
    set -l exclude_file "$HOME/.config/fd/.fdignore"
    local temp_ignore
    set temp_ignore $(mktemp)

    if test -f "$exclude_file" 
        # Copy existing patterns and ensure they work with full paths
        while IFS= read -r pattern || test -n "$"$$pattern"" ; do
            test -z "$"$$pattern"" || "$pattern" == \#*  && continue
            echo "$pattern" >> "$temp_ignore"
        done < "$exclude_file"
    fi

    echo "$temp_ignore"
end


function ff_help
    echo "Usage: ff test search_string test search_path"
    echo
    echo "Examples:"
    echo "  ff                         → search everything in \$HOME"
    echo "  ff notes                   → search for 'notes' under \$HOME"
    echo "  ff ~/projects              → search all in that path"
    echo "  ff todo ~/dev              → search for 'todo' in ~/dev"
    echo
    echo "After selection, choose an action:"
    echo "  - open       → xdg-open"
    echo "  - edit       → nvim"
    echo "  - copy       → wl-copy"
    echo "  - yazi       → open in yazi"
    echo "  - pcmanfm    → reveal in PCManFM"
    echo "  - cancel     → exit without action"
end
