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
        # No arguments - go to last working directory
        if test -n "$__last_working_dir" -a -d "$__last_working_dir" -a "$__last_working_dir" != "$PWD"
            set prev_dir "$PWD"
            echo "→ $__last_working_dir"
            builtin cd "$__last_working_dir"
            # Update last working dir to where we came from (for ping-pong effect)
            set -g __last_working_dir "$prev_dir"
            
            # Add current directory to history as "z triggered" if not already there
            set -l existing_index (contains -i "$prev_dir" $__dir_history)
            if test -n "$existing_index"
                # Remove existing entry and its reason
                set -e __dir_history[$existing_index]
                set -e __dir_history_reasons[$existing_index]
            end
            # Add to front with reason
            set __dir_history "$prev_dir" $__dir_history[1..9]
            set __dir_history_reasons "z triggered" $__dir_history_reasons[1..9]
        else if test (count $__dir_history) -gt 0 -a -n "$__dir_history[1]" -a -d "$__dir_history[1]"
            set prev_dir "$PWD"
            echo "→ $__dir_history[1]"
            builtin cd "$__dir_history[1]"
            # Update last working dir to where we came from
            set -g __last_working_dir "$prev_dir"
            
            # Add current directory to history as "z triggered"
            set -l existing_index (contains -i "$prev_dir" $__dir_history)
            if test -n "$existing_index"
                # Remove existing entry and its reason
                set -e __dir_history[$existing_index]
                set -e __dir_history_reasons[$existing_index]
            end
            # Add to front with reason
            set __dir_history "$prev_dir" $__dir_history[1..9]
            set __dir_history_reasons "z triggered" $__dir_history_reasons[1..9]
        else
            echo "No recent working directory found"
            return 1
        end
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
