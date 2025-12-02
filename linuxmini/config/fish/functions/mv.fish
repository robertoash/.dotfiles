# ~/.config/fish/functions/mv.fish
function mv -d "Move files and auto-update fre database"
    # Parse arguments to find source and destination
    set -l args
    for arg in $argv
        # Skip options (things starting with -)
        if not string match -q -- '-*' "$arg"
            set -a args "$arg"
        end
    end

    # Need at least 2 arguments (source and dest)
    set -l old_score
    if test (count $args) -ge 2; and command -q fre
        set -l source $args[-2]

        # Convert to absolute path for exact matching
        set -l abs_source (realpath "$source" 2>/dev/null)
        if test -z "$abs_source"
            set abs_source "$source"
        end

        # Get the old file's score before moving (exact path match)
        set old_score (fre --stat 2>/dev/null | grep -F "$abs_source" | awk '{print $1}')
    end

    # Call the real mv command
    command mv $argv
    set -l mv_status $status

    # Only proceed if mv succeeded and we found a score
    if test $mv_status -eq 0; and test -n "$old_score"; and command -q fre
        set -l source $args[-2]
        set -l dest $args[-1]

        # Convert source to absolute path for exact matching
        set -l abs_source (realpath "$source" 2>/dev/null)
        if test -z "$abs_source"
            set abs_source "$source"
        end

        # If dest is a directory, append the source filename
        if test -d "$dest"
            set dest "$dest/"(basename "$source")
        end

        # Convert destination to absolute path
        set -l abs_dest (realpath "$dest" 2>/dev/null)
        if test -z "$abs_dest"
            set abs_dest "$dest"
        end

        # Delete old entry using absolute path
        fre --delete "$abs_source" 2>/dev/null

        # Add new entry with absolute path and the old score
        fre --add "$abs_dest" 2>/dev/null

        # Increase to match old score (subtract 1 because --add already added 1 visit)
        # Validate old_score is a valid number before using it
        if string match -qr '^[0-9.]+$' "$old_score"
            set -l increase_amount (math "$old_score - 1")
            if test "$increase_amount" -gt 0
                fre --increase "$increase_amount" "$abs_dest" 2>/dev/null
            end
        end

        echo "✓ Migrated fre score ($old_score): $source → $abs_dest" >&2
    end

    return $mv_status
end
