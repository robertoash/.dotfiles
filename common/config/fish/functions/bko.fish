# ~/.config/fish/conf.d/06_buku_functions.fish
# Buku bookmark functions - loaded at startup for immediate availability

function fzf_multi_open
    set website (buku -p -f 5 | column -t -s (printf '\t') | fzfn --multi)

    for i in $website
        set index (echo "$i" | awk '{print $1}')
        buku -o "$index"
    end
end

function open_from_index
    set -l index $argv[1]
    buku -o "$index"
end

function open_first_match_from_string
    set -l arg $argv[1]
    set -l first_match (buku -p -f 5 | column -t -s (printf '\t') | fzf --filter="$arg")
    if test -n "$first_match"
        set -l index (echo "$first_match" | awk 'NR==1 {print $1}')
        buku -o "$index"
    end
end

# Helper function to extract and print URL based on fuzzy search
function fzf_url
    set -l first_match (buku -p -f 5 | column -t -s (printf '\t') | fzfn --no-multi)
    if test -n "$first_match"
        set -l index (echo "$first_match" | awk 'NR==1 {print $1}')
        set -l url (buku --format 1 -p "$index" | awk '{print $2}')
        echo "$url" | wl-copy
        echo "$url"
        echo "Copied to clipboard"
    end
end

function extract_url_from_index
    set -l index $argv[1]
    set -l url (buku --format 1 -p "$index" | awk '{print $2}')
    echo "$url" | wl-copy
    echo "$url"
    echo "Copied to clipboard"
end

function extract_url_from_string
    set -l arg $argv[1]
    set -l first_match (buku -p -f 5 | column -t -s (printf '\t') | fzf --filter="$arg")
    if test -n "$first_match"
        set -l index (echo "$first_match" | awk 'NR==1 {print $1}')
        set -l url (buku --format 1 -p "$index" | awk '{print $2}')
        echo "$url" | wl-copy
        echo "$url"
        echo "Copied to clipboard"
    end
end

# Main bko function
function bko
    if test -z "$argv[1]"
        fzf_multi_open
    else
        switch "$argv[1]"
            case --help
                echo "Usage: bko [OPTION] [INDEX/STRING]"
                echo "A helper function to open bookmarks using Buku with optional fuzzy search."
                echo
                echo "Options:"
                echo "  --help    Display this help message."
                echo "  --url     Extract and print URL based on fuzzy search."
                echo "            This option is mainly used to ouput URLs for other commands to use."
                echo
                echo "Usage without --url:"
                echo "  - Without any argument: Opens a multi-select fuzzy search to open multiple bookmarks."
                echo "  - With an index: Opens the bookmark at the given Buku index."
                echo "  - With a string: Performs a fuzzy search and opens the first match."
                echo
                echo "Usage with --url:"
                echo "  - Without any argument: Fuzzy search and print the selected URL."
                echo "  - With an index: Print the URL at the given Buku index."
                echo "  - With a string: Fuzzy search and print the first matching URL."
                echo
                echo "Examples:"
                    echo "  bko                # Open multi-select Buku fuzzy search to open multiple bookmarks."
    echo "  bko 1              # Open the bookmark at index 1."
    echo "  bko searchterm     # Fuzzy search and open the first match for 'searchterm'."
    echo "  bko --url          # Fuzzy search and print the selected URL."
    echo "  bko --url 1        # Print the URL at index 1."
    echo "  bko --url string   # Fuzzy search and print the first matching URL for 'string'."
                return
            case --url
                set argv $argv[2..-1]
                if test -z "$argv[1]"
                    fzf_url
                else
                    if string match -q -r '^[0-9]+$' -- "$argv[1]"
                        extract_url_from_index "$argv[1]"
                    else
                        extract_url_from_string "$argv[1]"
                    end
                end
                return
            case '*'
                if string match -q -r '^[0-9]+$' -- "$argv[1]"
                    open_from_index "$argv[1]"
                else
                    open_first_match_from_string "$argv[1]"
                end
                return
        end
    end
end
