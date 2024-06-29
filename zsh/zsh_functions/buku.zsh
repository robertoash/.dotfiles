bk_o() {
    if [ -z "$1" ]; then
        # Temporarily disable the preview for fzf
        local original_fzf_preview=$FZF_PREVIEW
        export FZF_PREVIEW=false
        set_fzf_alias

        # Save newline separated string into an array
        website=("${(@f)$(buku -p -f 5 | column -ts$'\t' | fzf --multi)}")

        # Restore the original fzf configuration
        export FZF_PREVIEW=$original_fzf_preview
        set_fzf_alias

        # Open each website
        for i in "${website[@]}"; do
            index="$(echo "$i" | awk '{print $1}')"
            buku -p "$index"
            buku -o "$index"
        done
    else
        # Determine if the argument is a number or a string
        if [[ "$1" =~ ^[0-9]+$ ]]; then
            # Argument is a number, open the bookmark with that index
            buku -o "$1"
        else
            # Argument is a string, perform a search and open
            arg=$1
            bk --np --oa "$arg"
        fi
    fi
}