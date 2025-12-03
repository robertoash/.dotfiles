# ~/.config/fish/functions/rm.fish
function rm -d "Remove files and auto-update fre database"
    # Collect files to be removed before actually removing them
    set -l files_to_check

    for arg in $argv
        # Skip options
        if not string match -q -- '-*' "$arg"
            # Store the path before deletion
            if test -e "$arg"
                set -a files_to_check "$arg"
            end
        end
    end

    # Call the real rm command
    command rm $argv
    set -l rm_status $status

    # Only proceed if rm succeeded and we have fre
    if test $rm_status -eq 0; and command -q fre
        # Remove each file from fre database using native command
        for file in $files_to_check
            fre --delete "$file" 2>/dev/null
            and echo "✓ Removed from fre database: $file" >&2
        end
    end

    return $rm_status
end
