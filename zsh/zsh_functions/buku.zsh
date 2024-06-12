bk_o() {
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
}
