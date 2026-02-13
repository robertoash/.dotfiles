# Smart ordering module with reasoning labels
# Orders completion candidates by context and tags them with reasons for ranking

function __completion_order
    # Arguments: context_type search_dir query_part
    # Returns: Ordered candidates with reasoning labels (tab-separated: path\tlabel)
    set -l context_type $argv[1]
    set -l search_dir $argv[2]
    set -l query_part $argv[3]

    set -l results

    switch $context_type
        case dirs
            # For cd/z/pushd: Immediate children first, then frecency-sorted

            # Step 1: Immediate children (depth 1) - these are most likely
            if test -d "$search_dir"
                for dir in (fd -Hi --no-ignore-vcs -t d --max-depth 1 . "$search_dir" 2>/dev/null)
                    echo "$dir	[child]"
                end
            end

            # Step 2: Zoxide directories (sorted by frecency rank)
            if command -q zoxide
                set -l zoxide_results (zoxide query -l 2>/dev/null | head -n 30)
                set -l rank 1
                for dir in $zoxide_results
                    echo "$dir	[z:$rank]"
                    set rank (math $rank + 1)
                end
            end

            # Step 3: Fre directories (if available)
            if command -q fre
                set -l fre_results (fre --sorted 2>/dev/null | string match -r '.*/$' | head -n 20)
                set -l rank 1
                for dir in $fre_results
                    echo "$dir	[fre:$rank]"
                    set rank (math $rank + 1)
                end
            end

            # Step 4: Deeper directories from filesystem
            if test -d "$search_dir"
                for dir in (fd -Hi --no-ignore-vcs -t d --min-depth 2 --max-depth 3 . "$search_dir" 2>/dev/null)
                    echo "$dir	[fs]"
                end
            end

        case files
            # For nvim/cat/bat: Recently edited files first

            # Step 1: Fre files (recently/frequently edited)
            if command -q fre
                set -l fre_results (fre --sorted 2>/dev/null | string match -v -r '.*/$' | head -n 20)
                set -l rank 1
                for file in $fre_results
                    echo "$file	[fre:$rank]"
                    set rank (math $rank + 1)
                end
            end

            # Step 2: Files in current directory (immediate context)
            if test -d "$search_dir"
                for file in (fd -Hi --no-ignore-vcs -t f --max-depth 1 . "$search_dir" 2>/dev/null)
                    echo "$file	[local]"
                end
            end

            # Step 3: Files in subdirectories
            if test -d "$search_dir"
                for file in (fd -Hi --no-ignore-vcs -t f --min-depth 2 --max-depth 3 . "$search_dir" 2>/dev/null)
                    echo "$file	[fs]"
                end
            end

        case both
            # For cp/mv/rsync: Mix of files and dirs, frecency-aware

            # Step 1: Frecency items (both files and dirs)
            if command -q zoxide
                set -l zoxide_results (zoxide query -l 2>/dev/null | head -n 15)
                for item in $zoxide_results
                    echo "$item	[z:freq]"
                end
            end

            if command -q fre
                set -l fre_results (fre --sorted 2>/dev/null | head -n 15)
                for item in $fre_results
                    echo "$item	[fre:freq]"
                end
            end

            # Step 2: Local files and directories
            if test -d "$search_dir"
                for item in (fd -Hi --no-ignore-vcs --max-depth 1 . "$search_dir" 2>/dev/null)
                    echo "$item	[local]"
                end
            end

            # Step 3: Deeper items
            if test -d "$search_dir"
                for item in (fd -Hi --no-ignore-vcs --min-depth 2 --max-depth 3 . "$search_dir" 2>/dev/null)
                    echo "$item	[fs]"
                end
            end
    end | awk '!seen[$1]++'  # Deduplicate by path, keeping first (highest priority)
end
