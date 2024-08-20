# Helper function to temporarily disable fzf preview
disable_fzf_preview() {
    original_fzf_preview=$FZF_PREVIEW
    export FZF_PREVIEW=false
    set_fzf_alias
}

# Helper function to restore fzf preview
restore_fzf_preview() {
    export FZF_PREVIEW=$original_fzf_preview
    set_fzf_alias
}

fzf_multi_open() {
    disable_fzf_preview
    website=("${(@f)$(buku -p -f 5 | column -ts$'\t' | fzf --multi)}")
    restore_fzf_preview

    for i in "${website[@]}"; do
        index=$(echo "$i" | awk '{print $1}')
        buku -o "$index"
    done
}

open_from_index() {
    local index=$1
    buku -o "$index"
}

open_first_match_from_string() {
    local arg=$1
    local first_match=$(buku -p -f 5 | column -ts$'\t' | fzf --filter="$arg")
    if [ -n "$first_match" ]; then
        local index=$(echo "$first_match" | awk 'NR==1 {print $1}')
        buku -o "$index"
    fi
}

# Helper function to extract and print URL based on fuzzy search
fzf_url() {
    local first_match=$(buku -p -f 5 | column -ts$'\t' | fzf --no-multi)
    if [ -n "$first_match" ]; then
        local index=$(echo "$first_match" | awk 'NR==1 {print $1}')
        local url=$(buku --format 1 -p "$index" | awk '{print $2}')
        echo "$url"
    fi
}

extract_url_from_index() {
    local index=$1
    local url=$(buku --format 1 -p "$index" | awk '{print $2}')
    echo "$url"
}

extract_url_from_string() {
    local arg=$1
    local first_match=$(buku -p -f 5 | column -ts$'\t' | fzf --filter="$arg")
    if [ -n "$first_match" ]; then
        local index=$(echo "$first_match" | awk 'NR==1 {print $1}')
        local url=$(buku --format 1 -p "$index" | awk '{print $2}')
        echo "$url"
    fi
}

# Main function
bk_o() {
    if [ -z "$1" ]; then
        fzf_multi_open
    else
        case "$1" in
            --url)
                shift
                if [ -z "$1" ]; then
                    disable_fzf_preview
                    fzf_url
                    restore_fzf_preview
                else
                    case "$1" in
                        [0-9]*)
                            extract_url_from_index "$1"
                            ;;
                        *)
                            extract_url_from_string "$1"
                            ;;
                    esac
                fi
                return
                ;;
            [0-9]*)
                open_from_index "$1"
                return
                ;;
            *)
                open_first_match_from_string "$1"
                return
                ;;
        esac
    fi
}
