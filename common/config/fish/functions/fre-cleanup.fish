# ~/.config/fish/functions/fre-cleanup.fish
function fre-cleanup -d "Remove non-existent files from fre database"
    if not command -q fre
        echo "Error: fre not found" >&2
        return 1
    end

    echo "Scanning fre database for non-existent files..."
    echo ""

    set -l removed 0
    set -l total 0

    # Get all tracked items
    for line in (fre --stat 2>/dev/null)
        set total (math $total + 1)
        set -l path (echo $line | awk '{$1=""; print substr($0,2)}')

        # Convert relative to absolute if needed
        set -l full_path "$path"
        if not string match -q '/*' -- "$path"
            set full_path "$HOME/$path"
        end

        # Check if file exists
        if not test -e "$full_path"
            echo "Removing: $path"
            fre --delete "$path" 2>/dev/null
            set removed (math $removed + 1)
        end
    end

    echo ""
    echo "Cleanup complete:"
    echo "  Scanned: $total items"
    echo "  Removed: $removed items"
end
