# Multi-source completion candidate engine
# Merges frecency data (zoxide, fre), fish history paths, and filesystem results (fd)
# with smart deduplication and prioritization

function __completion_sources --argument-names type search_dir query_part
    # type: "dirs", "files", or "both"
    # search_dir: directory to search in (default ".")
    # query_part: partial text the user has typed (for fzf --query, not for filtering here)
    #
    # Outputs candidates to stdout, one per line, ordered by priority:
    #   1. Frecency results (zoxide for dirs, fre for files)
    #   2. Fish history paths (extracted from command history)
    #   3. Filesystem results via fd (shallow first, then deep)
    #
    # The caller pipes this into fzf.

    test -z "$search_dir"; and set search_dir "."

    set -l candidates

    switch $type
        case dirs
            # Source 1: zoxide frecency (dirs only)
            if command -q zoxide; and test "$search_dir" = "."
                # Only use zoxide for CWD-relative completion (not when searching a specific path)
                set -a candidates (zoxide query -l 2>/dev/null | head -n 30)
            end

            # Source 2: fish history paths (extract directory arguments from history)
            if test "$search_dir" = "."
                set -a candidates (builtin history search --max 500 --prefix cd 2>/dev/null | string replace -r '^cd\s+' '' | string match -r '^[~/.].*' | head -n 20)
            end

            # Source 3: fd filesystem (shallow then deep, respects ~/.config/fd/ignore)
            set -a candidates (fd -Hi -t d --max-depth 1 . "$search_dir" 2>/dev/null)
            set -a candidates (fd -Hi -t d --min-depth 2 . "$search_dir" 2>/dev/null)

        case files
            # Source 1: fre frecency (files only)
            if command -q fre; and test "$search_dir" = "."
                set -a candidates (fre --sorted 2>/dev/null | head -n 30)
            end

            # Source 2: fish history paths (extract file arguments from history)
            if test "$search_dir" = "."
                set -a candidates (builtin history search --max 500 2>/dev/null | string replace -r '^\S+\s+' '' | string match -r '^[~/.].*\.\w+$' | head -n 20)
            end

            # Source 3: fd filesystem (shallow then deep, respects ~/.config/fd/ignore)
            set -a candidates (fd -Hi -t f --max-depth 1 . "$search_dir" 2>/dev/null)
            set -a candidates (fd -Hi -t f --min-depth 2 . "$search_dir" 2>/dev/null)

        case both
            # Source 1: frecency (both zoxide and fre)
            if command -q zoxide; and test "$search_dir" = "."
                set -a candidates (zoxide query -l 2>/dev/null | head -n 15)
            end
            if command -q fre; and test "$search_dir" = "."
                set -a candidates (fre --sorted 2>/dev/null | head -n 15)
            end

            # Source 2: fish history paths (extract path arguments from history)
            if test "$search_dir" = "."
                set -a candidates (builtin history search --max 500 2>/dev/null | string replace -r '^\S+\s+' '' | string match -r '^[~/.].*' | head -n 20)
            end

            # Source 3: fd filesystem (shallow then deep, both types, respects ~/.config/fd/ignore)
            set -a candidates (fd -Hi --max-depth 1 . "$search_dir" 2>/dev/null)
            set -a candidates (fd -Hi --min-depth 2 . "$search_dir" 2>/dev/null)
    end

    # Deduplicate while preserving priority order (first occurrence wins)
    printf '%s\n' $candidates | awk '!seen[$0]++'
end
