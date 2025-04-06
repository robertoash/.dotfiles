# Tell fzf-completion to use `fd` instead of `find` or default walker
_fzf_compgen_path() {
  fd --type f --type d --hidden --follow --full-path --strip-cwd-prefix "${1:-.}"
}

_fzf_compgen_dir() {
  fd --type d --hidden --follow --full-path --strip-cwd-prefix "${1:-.}"
}

# Fzf configs
# 🧠 User-friendly wrapper configs
export FZF_CONFIG_DEFAULT="fzf --preview 'bat --color=always {}' --preview-window '~3' --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff'"
export FZF_CONFIG_NO_PREVIEW="fzf --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff'"
export FZF_PREVIEW=true  # ✅ Used for conditional logic in scripts
export FZF_DEFAULT_COMMAND='fd . --type f --type d --hidden --follow --strip-cwd-prefix'

# 🔍 Completion & fuzzy matching
export FZF_COMPLETION_OPTS="\
  --preview '$HOME/.config/fzf/fzf_preview.sh {}' \
  --height 40% --reverse --ansi \
  --preview-window "right:50%" \
  --preview-window '~3' \
  --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff' \
  --scheme=path \
  --walker=file,dir,follow,hidden \
  --tiebreak=begin,length,index"
export FZF_COMPLETION_TRIGGER=''  # Trigger on every Tab (aggressive)
export FZF_COMPLETION_DIR_OPTS="--min-depth=1 --max-depth=3"

# 📂 Fuzzy file/dir browsing
export FZF_CTRL_T_COMMAND="fd --type f --type d --hidden --follow"
export FZF_ALT_C_COMMAND="fd --type d --hidden --follow"
# export FZF_DEFAULT_COMMAND='find . \! \( -type d -path ./.git -prune \) \! -type d \! -name '\''*.tags'\'' -printf '\''%P\n'\'
