function hdel --description 'Delete history entries matching a pattern'
    set -l regex_mode 0
    set -l pattern ""

    # Parse arguments
    for arg in $argv
        if test "$arg" = "-r"
            set regex_mode 1
        else
            set pattern "$arg"
        end
    end

    if test -z "$pattern"
        echo "Usage: hdel [-r] PATTERN"
        echo "  -r    Use regex matching"
        echo ""
        echo "Examples:"
        echo "  hdel 'ssh workbmp'     # Delete entries containing this string"
        echo "  hdel -r 'ssh.*bmp'     # Delete entries matching regex"
        return 1
    end

    # Get matching history entries
    set -l matches
    if test $regex_mode -eq 1
        # Regex mode: filter history with string match
        set matches (history | string match -r "$pattern")
    else
        # Contains mode: use glob pattern (literal string matching)
        set matches (history | string match "*$pattern*")
    end

    if test (count $matches) -eq 0
        echo "No matching history entries found."
        return 0
    end

    echo "Found "(count $matches)" matching entries:"
    for entry in $matches
        echo "  $entry"
    end

    echo ""
    read -l -P "Delete these entries? [y/N] " confirm

    if test "$confirm" = "y" -o "$confirm" = "Y"
        for entry in $matches
            history delete --exact --case-sensitive "$entry"
        end
        echo "Deleted "(count $matches)" entries."
    else
        echo "Cancelled."
    end
end
