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

        # Get the old file's score before moving
        set old_score (fre --stat 2>/dev/null | grep -F "$source" | awk '{print $1}')
    end

    # Call the real mv command
    command mv $argv
    set -l mv_status $status

    # Only proceed if mv succeeded and we found a score
    if test $mv_status -eq 0; and test -n "$old_score"; and command -q fre
        set -l source $args[-2]
        set -l dest $args[-1]

        # If dest is a directory, append the source filename
        if test -d "$dest"
            set dest "$dest/"(basename "$source")
        end

        # Delete old entry
        fre --delete "$source" 2>/dev/null

        # Add new entry with the old score
        fre --add "$dest" 2>/dev/null

        # Increase to match old score (subtract 1 because --add already added 1 visit)
        set -l increase_amount (math "$old_score - 1")
        if test (math "$increase_amount > 0") = 1
            fre --increase "$increase_amount" "$dest" 2>/dev/null
        end

        echo "✓ Migrated fre score ($old_score): $source → $dest" >&2
    end

    return $mv_status
end
