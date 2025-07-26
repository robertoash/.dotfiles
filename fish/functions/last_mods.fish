function last_mods --description 'List files/dirs sorted by modification time using fd'
    set -l recursive ""
    set -l type_filter ""
    
    # Parse arguments
    for arg in $argv
        switch $arg
            case --recursive
                set recursive "-r"
            case --files
                set type_filter "file"
            case --dirs --directories
                set type_filter "directory"
            case --all
                set type_filter ""  # Show both files and dirs
            case '-*'
                # Parse combined flags (e.g., -rf, -ar, etc.)
                set -l chars (string split "" (string sub --start 2 -- $arg))
                for char in $chars
                    switch $char
                        case r
                            set recursive "-r"
                        case f
                            set type_filter "file"
                        case d
                            set type_filter "directory"
                        case a
                            set type_filter ""  # Show both files and dirs
                        case '*'
                            echo "Unknown option: -$char" >&2
                            echo "Usage: last_mods [-r] [-f|-d|-a]" >&2
                            echo "  -r, --recursive    Search recursively" >&2
                            echo "  -f, --files        Show only files" >&2
                            echo "  -d, --dirs         Show only directories" >&2
                            echo "  -a, --all          Show both files and directories" >&2
                            return 1
                    end
                end
        end
    end
    
    # Execute fd and sort by modification time (most recent at bottom)
    if test -z "$recursive"
        # Non-recursive: use --max-depth 1
        if test -z "$type_filter"
            # No type filter - show both files and dirs
            fd -H --no-ignore --max-depth 1 --exec-batch eza --all --color=always --icons --group-directories-first --git -Hah -l -a -d --sort=modified
        else
            # With type filter
            fd -H --no-ignore -t $type_filter --max-depth 1 --exec-batch eza --all --color=always --icons --group-directories-first --git -Hah -l -a -d --sort=modified
        end
    else
        # Recursive: no max-depth limit
        if test -z "$type_filter"
            # No type filter - show both files and dirs
            fd -H --no-ignore --exec-batch eza --all --color=always --icons --group-directories-first --git -Hah -l -a -d --sort=modified
        else
            # With type filter
            fd -H --no-ignore -t $type_filter --exec-batch eza --all --color=always --icons --group-directories-first --git -Hah -l -a -d --sort=modified
        end
    end
end
