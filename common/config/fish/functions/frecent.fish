# ~/.config/fish/functions/frecent.fish
function frecent
    argparse 'd/dirs' 'f/files' 'a/all' 'i/interactive' 'h/help' -- $argv
    or return

    if set -q _flag_help
        echo "Usage: frecent [OPTIONS]"
        echo "  -d, --dirs        Show directories only (zoxide)"
        echo "  -f, --files       Show files only (fre)"
        echo "  -a, --all         Show both directories and files"
        echo "  -i, --interactive Use fzf for interactive selection"
        echo "  -h, --help        Show this help"
        echo ""
        echo "Default behavior (no flags): --all"
        echo ""
        echo "Examples:"
        echo "  frecent -d        # List directories"
        echo "  frecent -f -i     # Interactive file selection"
        echo "  frecent -a -i     # Interactive selection from all"
        echo "  nvim (frecent -f -i)  # Edit file interactively"
        return
    end

    set -l items

    if set -q _flag_dirs
        # Only directories from zoxide
        if command -q zoxide
            set items (zoxide query --list 2>/dev/null)
        else
            echo "Error: zoxide not found" >&2
            return 1
        end
    else if set -q _flag_files
        # Only files from fre
        if command -q fre
            set items (fre --sorted 2>/dev/null)
        else
            echo "Error: fre not found" >&2
            return 1
        end
    else
        # Default: both directories and files
        set -l dirs
        set -l files

        if command -q zoxide
            set dirs (zoxide query --list 2>/dev/null)
        end

        if command -q fre
            set files (fre --sorted 2>/dev/null)
        end

        # Combine both, directories first
        set items $dirs $files
    end

    # Filter out empty results and duplicates
    if test (count $items) -eq 0
        echo "No frecent items found" >&2
        return 1
    end

    # Remove duplicates while preserving order
    set -l unique_items
    for item in $items
        if not contains "$item" $unique_items
            set -a unique_items "$item"
        end
    end

    if set -q _flag_interactive
        if command -q fzf
            printf "%s\n" $unique_items | fzf --height=40% --reverse --border
        else
            echo "Error: fzf not found for interactive mode" >&2
            return 1
        end
    else
        printf "%s\n" $unique_items
    end
end

# Helper wrapper functions for common interactive use cases
function fcd
    set -l dir (frecent --dirs --interactive)
    if test -n "$dir"
        cd "$dir"
    end
end

function fvim
    set -l file (frecent --files --interactive)
    if test -n "$file"
        nvim "$file"
    end
end

function fopen
    set -l item (frecent --all --interactive)
    if test -n "$item"
        if test -d "$item"
            cd "$item"
        else if test -f "$item"
            nvim "$item"
        end
    end
end


