# Temporarily cd to a directory, run commands, then return to original directory
# Usage: cdtemp <directory> <command> [args...]
# Example: cdtemp ~/.config touch temp.txt

function cdtemp
    set -l original_dir $PWD

    if test (count $argv) -lt 2
        echo "Usage: cdtemp <directory> <command> [args...]" >&2
        return 1
    end

    set -l target_dir $argv[1]
    set -l cmd $argv[2..-1]

    if not cd "$target_dir" 2>&1
        echo "cdtemp: cannot cd to '$target_dir'" >&2
        return 1
    end

    # Run the command, capture exit status
    $cmd
    set -l cmd_status $status

    # Always return to original directory
    cd "$original_dir"

    return $cmd_status
end
