# Function to set the fzf alias based on FZF_PREVIEW
function set_fzf_alias
    if test "$FZF_PREVIEW" = true
        alias fzf="$FZF_CONFIG_DEFAULT"
    else
        alias fzf="$FZF_CONFIG_NO_PREVIEW"
    end
end