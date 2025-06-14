function __smart_cwd_hook --on-variable PWD
    set -l current_path (string replace $HOME '~' $PWD)
    set -l path_parts (string split '/' -- $current_path)
    set -l depth (count $path_parts)

    set -l keep_first 2
    set -l keep_last 2
    set -l keep_middle 1  # Set to 0 to hide middle part entirely
    set -l min_depth_for_compression 6

    # If path is short enough, just use it as-is
    if test $depth -le $min_depth_for_compression
        set -gx SMART_CWD $current_path
        return
    end

    # Path needs compression
    set -l first_parts $path_parts[1..$keep_first]
    set -l last_parts $path_parts[(math $depth - $keep_last + 1)..$depth]

    # Calculate middle range
    set -l middle_start (math $keep_first + 1)
    set -l middle_end (math $depth - $keep_last)

    if test $middle_end -ge $middle_start; and test $keep_middle -gt 0
        # Show the middle element (same logic as before)
        set -l middle_count (math $middle_end - $middle_start + 1)
        set -l half_count (math "floor($middle_count / 2)")
        set -l middle_index (math $middle_start + $half_count)
        set -l middle_part $path_parts[$middle_index]

        # Build: first/.../middle/.../last
        set -l compressed_parts $first_parts
        set compressed_parts $compressed_parts "..."
        set compressed_parts $compressed_parts $middle_part
        set compressed_parts $compressed_parts "..."
        set compressed_parts $compressed_parts $last_parts

        set -gx SMART_CWD (string join "/" $compressed_parts)
    else
        # keep_middle = 0: Skip middle part entirely
        set -l compressed_parts $first_parts
        set compressed_parts $compressed_parts "..."
        set compressed_parts $compressed_parts $last_parts

        set -gx SMART_CWD (string join "/" $compressed_parts)
    end
end