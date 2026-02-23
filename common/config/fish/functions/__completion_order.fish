# Smart ordering module with reasoning labels
# Default ordering: local (depth 1) → deeper (depth 2-3) → frecency (only when no path typed)
# Exceptions to this default are documented in the switch block below.

function __completion_order
    # Arguments: context_type search_dir query_part
    # Returns: Ordered candidates with reasoning labels (tab-separated: path\tlabel)
    set -l context_type $argv[1]
    set -l search_dir $argv[2]
    set -l query_part $argv[3]

    # Get terminal width for right-justified labels (reserve 15 chars for label + margin)
    set -l term_width (tput cols 2>/dev/null || echo 80)
    set -l label_space 15
    set -l path_width (math $term_width - $label_space)

    # Helper function to format path with right-justified label
    function __format_with_label -a path label max_width
        set -l path_len (string length -- "$path")
        if test $path_len -lt $max_width
            set -l padding (math $max_width - $path_len)
            set -l spaces (string repeat -n $padding ' ')
            echo "$path$spaces	$label"
        else
            # Path too long, just add tab separator
            echo "$path	$label"
        end
    end

    # Defaults - overridden per context below
    set -l fd_type_flag          # no type filter = both files and dirs
    set -l use_zoxide true
    set -l use_fre true

    # Exceptions to default ordering/sources:
    # - dirs: restrict to directories only; zoxide replaces fre (dir frecency, not file frecency)
    # - files: restrict to files only; fre replaces zoxide (file frecency, not dir frecency)
    switch $context_type
        case dirs
            set fd_type_flag -t d
            set use_fre false
        case files
            set fd_type_flag -t f
            set use_zoxide false
    end

    # Step 1: Immediate children (depth 1)
    if test -d "$search_dir"
        for item in (fd -Hi --no-ignore $fd_type_flag --max-depth 1 . "$search_dir" 2>/dev/null)
            __format_with_label "$item" "[local]" $path_width
        end
    end

    # Step 2: Deeper items (depth 2-3)
    if test -d "$search_dir"
        for item in (fd -Hi --no-ignore $fd_type_flag --min-depth 2 --max-depth 3 . "$search_dir" 2>/dev/null)
            __format_with_label "$item" "[fd]" $path_width
        end
    end

    # Step 3: Frecency - only when no specific path was typed
    if test "$search_dir" = "."
        if test "$use_zoxide" = true; and command -q zoxide
            set -l rank 1
            for item in (zoxide query -l 2>/dev/null | head -n 15)
                __format_with_label "$item" "[z:$rank]" $path_width
                set rank (math $rank + 1)
            end
        end

        if test "$use_fre" = true; and command -q fre
            set -l rank 1
            set -l fre_entries
            # files: exclude dirs (no trailing slash); both: include everything
            if test "$context_type" = files
                set fre_entries (fre --sorted 2>/dev/null | string match -v -r '.*/$' | head -n 20)
            else
                set fre_entries (fre --sorted 2>/dev/null | head -n 15)
            end
            for item in $fre_entries
                __format_with_label "$item" "[fre:$rank]" $path_width
                set rank (math $rank + 1)
            end
        end
    end

end | awk '!seen[$1]++'  # Deduplicate by path, keeping first (highest priority)
