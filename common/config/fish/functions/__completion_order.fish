# Smart ordering module with reasoning labels
# Orders completion candidates by context and tags them with reasons for ranking

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

    set -l results

    switch $context_type
        case dirs
            # For cd/z/pushd: Immediate children first, then frecency-sorted

            # Step 1: Immediate children (depth 1) - these are most likely
            if test -d "$search_dir"
                for dir in (fd -Hi --no-ignore -t d --max-depth 1 . "$search_dir" 2>/dev/null)
                    __format_with_label "$dir" "[child]" $path_width
                end
            end

            # Step 2: Zoxide directories (sorted by frecency rank)
            if command -q zoxide
                set -l zoxide_results (zoxide query -l 2>/dev/null | head -n 30)
                set -l rank 1
                for dir in $zoxide_results
                    __format_with_label "$dir" "[z:$rank]" $path_width
                    set rank (math $rank + 1)
                end
            end

            # Step 3: Fre directories (if available)
            if command -q fre
                set -l fre_results (fre --sorted 2>/dev/null | string match -r '.*/$' | head -n 20)
                set -l rank 1
                for dir in $fre_results
                    __format_with_label "$dir" "[fre:$rank]" $path_width
                    set rank (math $rank + 1)
                end
            end

            # Step 4: Deeper directories from filesystem
            if test -d "$search_dir"
                for dir in (fd -Hi --no-ignore -t d --min-depth 2 --max-depth 3 . "$search_dir" 2>/dev/null)
                    __format_with_label "$dir" "[fd]" $path_width
                end
            end

        case files
            # For nvim/cat/bat: Recently edited files first

            # Step 1: Fre files (recently/frequently edited)
            if command -q fre
                set -l fre_results (fre --sorted 2>/dev/null | string match -v -r '.*/$' | head -n 20)
                set -l rank 1
                for file in $fre_results
                    __format_with_label "$file" "[fre:$rank]" $path_width
                    set rank (math $rank + 1)
                end
            end

            # Step 2: Files in current directory (immediate context)
            if test -d "$search_dir"
                for file in (fd -Hi --no-ignore -t f --max-depth 1 . "$search_dir" 2>/dev/null)
                    __format_with_label "$file" "[local]" $path_width
                end
            end

            # Step 3: Files in subdirectories
            if test -d "$search_dir"
                for file in (fd -Hi --no-ignore -t f --min-depth 2 --max-depth 3 . "$search_dir" 2>/dev/null)
                    __format_with_label "$file" "[fd]" $path_width
                end
            end

        case both
            # For cp/mv/rsync: Mix of files and dirs, frecency-aware

            # Step 1: Frecency items (both files and dirs)
            if command -q zoxide
                set -l zoxide_results (zoxide query -l 2>/dev/null | head -n 15)
                for item in $zoxide_results
                    __format_with_label "$item" "[z:freq]" $path_width
                end
            end

            if command -q fre
                set -l fre_results (fre --sorted 2>/dev/null | head -n 15)
                for item in $fre_results
                    __format_with_label "$item" "[fre:freq]" $path_width
                end
            end

            # Step 2: Local files and directories
            if test -d "$search_dir"
                for item in (fd -Hi --no-ignore --max-depth 1 . "$search_dir" 2>/dev/null)
                    __format_with_label "$item" "[local]" $path_width
                end
            end

            # Step 3: Deeper items
            if test -d "$search_dir"
                for item in (fd -Hi --no-ignore --min-depth 2 --max-depth 3 . "$search_dir" 2>/dev/null)
                    __format_with_label "$item" "[fd]" $path_width
                end
            end
    end | awk '!seen[$1]++'  # Deduplicate by path, keeping first (highest priority)
end
