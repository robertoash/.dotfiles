# Function to set the fzf alias based on FZF_PREVIEW
set_fzf_alias() {
    if [ "$FZF_PREVIEW" = true ]; then
        alias fzf="$FZF_CONFIG_DEFAULT"
    else
        alias fzf="$FZF_CONFIG_NO_PREVIEW"
    fi
}
# Initialize the fzf alias
set_fzf_alias

