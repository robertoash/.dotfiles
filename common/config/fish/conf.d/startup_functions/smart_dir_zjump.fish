# Configuration - adjust this threshold as needed
set -g __dir_time_threshold 30  # seconds spent to consider a directory "working"

# Initialize variables immediately
if not set -q __dir_history
    set -g __dir_history
end

if not set -q __dir_history_reasons
    set -g __dir_history_reasons
end

if not set -q __dir_start_time
    set -g __dir_start_time (date +%s)
end

if not set -q __last_working_dir
    if test "$PWD" != "$HOME"
        set -g __last_working_dir "$PWD"
        # Add initial directory to history
        if not contains "$PWD" $__dir_history
            set -g __dir_history "$PWD"
            set -g __dir_history_reasons "init"
        end
    else
        set -g __last_working_dir "$HOME"
    end
end

# Track the previous PWD ourselves since we can't get it from Fish
if not set -q __tracked_pwd
    set -g __tracked_pwd "$PWD"
end

# Function to track directory entry time
function __track_dir_entry --on-variable PWD
    set current_time (date +%s)
    
    # Use our tracked PWD as the previous directory
    set previous_dir "$__tracked_pwd"
    
    # Check if we spent enough time in the previous directory to consider it "working"
    if test $__dir_start_time -ne 0; and test -n "$previous_dir"; and test "$previous_dir" != "$PWD"
        set time_spent (math "$current_time - $__dir_start_time")
        if test $time_spent -gt $__dir_time_threshold
            # Previous directory qualifies as "working" - update last_working_dir
            if test "$previous_dir" != "$HOME"
                set -g __last_working_dir "$previous_dir"
                # Also add to history (remove if already there, then add to front)
                set -l existing_index (contains -i "$previous_dir" $__dir_history)
                if test -n "$existing_index"
                    # Remove existing entry and its reason
                    set -e __dir_history[$existing_index]
                    set -e __dir_history_reasons[$existing_index]
                end
                # Add to front with reason
                set __dir_history "$previous_dir" $__dir_history[1..9]  # Keep last 10
                set __dir_history_reasons (printf "%ds spent" $time_spent) $__dir_history_reasons[1..9]
            end
        end
    end
    
    # Update our tracked PWD and start time for the new directory
    set -g __tracked_pwd "$PWD"
    set -g __dir_start_time $current_time
end

# Smart z function
function z --description 'Smart directory jumping with recent fallback'
    if test (count $argv) -eq 0
        # No arguments - open fzf directory picker
        set -l fzf_input

        # Build fzf input: Last dir (yellow) at top, then zoxide dirs
        if test -n "$__last_working_dir" -a -d "$__last_working_dir" -a "$__last_working_dir" != "$PWD"
            # Prepend yellow-highlighted Last dir
            set fzf_input (printf '\e[33m%s\e[0m\n' "$__last_working_dir")
        end

        # Append zoxide dirs (exclude PWD and __last_working_dir to avoid duplicates)
        set -l zoxide_dirs (zoxide query -l | string match -v "$PWD" | string match -v "$__last_working_dir")
        if test -n "$zoxide_dirs"
            set fzf_input $fzf_input $zoxide_dirs
        end

        # If no dirs available, show message and return
        if test (count $fzf_input) -eq 0
            echo "No recent directories found"
            return 1
        end

        # Pipe into fzf with proper options
        set -l selected (printf '%s\n' $fzf_input | command fzf \
            --ansi \
            --height 40% \
            --reverse \
            --no-sort \
            --header 'cd to...' \
            --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff')

        # Handle selection
        if test -n "$selected"
            # Strip ANSI codes from selected result
            set selected (string replace -ra '\e\[[0-9;]*m' '' -- "$selected")

            # Verify it's a valid directory and navigate
            if test -d "$selected"
                set prev_dir "$PWD"
                builtin cd "$selected"
                # Update last working dir to where we came from
                set -g __last_working_dir "$prev_dir"

                # Add previous directory to history as "z triggered"
                set -l existing_index (contains -i "$prev_dir" $__dir_history)
                if test -n "$existing_index"
                    # Remove existing entry and its reason
                    set -e __dir_history[$existing_index]
                    set -e __dir_history_reasons[$existing_index]
                end
                # Add to front with reason
                set __dir_history "$prev_dir" $__dir_history[1..9]
                set __dir_history_reasons "z triggered" $__dir_history_reasons[1..9]
            end
        end
        # If selection is empty (user cancelled), do nothing and return 0
        return 0
    else
        # With arguments - use zoxide for frecency-based jumping
        set prev_dir "$PWD"
        __zoxide_z $argv
        # If successful, update last working dir and add to history
        if test $status -eq 0
            set -g __last_working_dir "$prev_dir"

            # Add previous directory to history as "z triggered"
            set -l existing_index (contains -i "$prev_dir" $__dir_history)
            if test -n "$existing_index"
                # Remove existing entry and its reason
                set -e __dir_history[$existing_index]
                set -e __dir_history_reasons[$existing_index]
            end
            # Add to front with reason
            set __dir_history "$prev_dir" $__dir_history[1..9]
            set __dir_history_reasons "z triggered" $__dir_history_reasons[1..9]
        end
    end
end

# Optional: function to see your working directory history
function zh --description 'Show recent working directories'
    echo "Marking threshold: $__dir_time_threshold secs"
    echo "Last working directory: $__last_working_dir"
    echo "Recent marked directories:"
    
    # Check if current directory qualifies for the list
    set current_time (date +%s)
    set time_in_current (math "$current_time - $__dir_start_time")
    
    set display_history $__dir_history
    set display_reasons $__dir_history_reasons
    
    if test $time_in_current -gt $__dir_time_threshold; and test "$PWD" != "$HOME"
        # Check if PWD is already in history
        if not contains "$PWD" $__dir_history
            # Add current directory temporarily for display
            set display_history "$PWD" $display_history
            set display_reasons (printf "current - %ds spent" $time_in_current) $display_reasons
        end
    end
    
    set count (count $display_history)
    if test $count -gt 10
        set count 10
    end
    for i in (seq 1 $count)
        echo "  $i: $display_history[$i] ($display_reasons[$i])"
    end
end
