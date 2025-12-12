# ~/.config/fish/conf.d/04_fzf.fish
# FZF Configuration

# Fzf configs
# 🧠 User-friendly wrapper configs
set -gx FZF_CONFIG_DEFAULT "fzf --preview '$HOME/.config/fzf/fzf_preview.sh {}' --preview-window '~3' --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff'"
set -gx FZF_CONFIG_NO_PREVIEW "fzf --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff'"
set -gx FZF_CONFIG_INLINE "fzf --height=30% --layout=reverse --border=none --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff'"

# Initialize fzf for fish lazily (on first prompt)
if command -v fzf >/dev/null 2>&1
    function __fzf_init_once --on-event fish_prompt
        # Only run once
        if not set -q __fzf_initialized
            fzf --fish | source
            set -g __fzf_initialized 1
            functions -e __fzf_init_once  # Remove this function after running
        end
    end
end

function fzfp
    eval $FZF_CONFIG_DEFAULT $argv
end

function fzfn
    eval $FZF_CONFIG_NO_PREVIEW $argv
end

function fzfi
    eval $FZF_CONFIG_INLINE $argv
end


function fzf
    if test (count $argv) -gt 0
        # If user passes args, call the real fzf with them (skip our default)
        command fzf $argv
    else
        # No args? Use the default config (with preview)
        eval $FZF_CONFIG_DEFAULT
    end
end

