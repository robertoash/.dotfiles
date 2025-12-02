# ~/.config/zsh/.zshrc

# #################################
# # History & Cache
# #################################

export HISTSIZE=10000
export SAVEHIST=10000
export HISTCONTROL=ignoreboth
if [[ -z "$SECURE_SHELL" ]]; then
  export HISTFILE="$HOME/.cache/zsh_history"
fi


# #################################
# # Environment Variables
# #################################

source ~/.config/zsh/sources/.zsh_envs


# #################################
# # Options
# #################################

unsetopt menu_complete
unsetopt flowcontrol
setopt glob_dots
setopt prompt_subst
setopt always_to_end
setopt append_history
setopt auto_menu
setopt complete_in_word
setopt extended_history
setopt hist_expire_dups_first
setopt hist_ignore_dups
setopt hist_ignore_space
setopt hist_verify
setopt inc_append_history_time
setopt share_history
setopt NO_BEEP

# Enable right prompt (RPROMPT) support
# for starship prompt
setopt prompt_subst

# Enable menu selection for completions
zstyle ':completion:*' menu select
fpath=(${ASDF_DATA_DIR:-$HOME/.asdf}/completions $fpath) # append asdf completions to fpath
autoload -Uz compinit && compinit # initialise completions with ZSH's compinit


# #################################
# # Autocompletion priority
# #################################

if [[ -z "$SECURE_SHELL" ]]; then
  # Activate fasd (easy file and dir jump)
  eval "$(fasd --init auto)"
  unalias z 2>/dev/null # Reclaim z command
  unalias zz 2>/dev/null # Reclaim zz command
fi

# #################################
# # Sourcing
# #################################

# Path setting
source ~/.config/zsh/sources/.zsh_path
# Hooks
source ~/.config/zsh/sources/.zsh_hooks
# Fzf defaults
source ~/.config/zsh/sources/.zsh_fzf_config.zsh
# Aliases
source ~/.config/zsh/sources/.zsh_aliases
# Plugins
source ~/.config/zsh/plugins/fzf-tab/fzf-tab.plugin.zsh
source ~/.config/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source ~/.config/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
source ~/.config/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh
# Functions
for f in ~/.config/zsh/zsh_functions/*.zsh; do
    source "$f"
done
# Broot
source ~/.config/broot/launcher/bash/br
# Prompt Customization & Utilities
[[ ! -f ~/.config/zsh/sources/.p10k.zsh ]] || source ~/.config/zsh/sources/.p10k.zsh
# Keybindings
source ~/.config/zsh/sources/.zsh_keybinds.zsh

# #################################
# # Completion Overrides
# #################################

# Git branch completion
zstyle ':completion:*:git-checkout:*' sort false
# Group support for descriptions
zstyle ':completion:*:descriptions' format '[%d]'
# Use LS_COLORS to style filenames
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}

# #################################
# # Miscellaneous Configurations
# #################################

# Auto Notify
AUTO_NOTIFY_IGNORE+=("lf" "hugo serve" "rofi")
# Suggestion Strategy
ZSH_AUTOSUGGEST_STRATEGY=(match_prev_cmd history)
ZSH_AUTOSUGGEST_USE_ASYNC=1
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE="fg=#89b4fa"


# #################################
# # App Specific Commands
# #################################

# Thefuck
eval "$(thefuck --alias fuck)"
# Hass cli
eval "$(_HASS_CLI_COMPLETE=source_zsh hass-cli)"
# Load Google Cloud SDK
if [ -f '/home/rash/builds/google-cloud-sdk/path.zsh.inc' ]; then
    source '/home/rash/builds/google-cloud-sdk/path.zsh.inc'
fi
# Load Google Cloud SDK completion with proper initialization
if [ -f '/home/rash/builds/google-cloud-sdk/completion.zsh.inc' ]; then
    # Load Google Cloud SDK completion
    source '/home/rash/builds/google-cloud-sdk/completion.zsh.inc'
fi
# Activate walk file manager
function lk {
  cd "$(walk --icons --with-border --fuzzy "$@")"
}
if [[ -z "$SECURE_SHELL" ]]; then
  #zoxide
  eval "$(zoxide init zsh)"
  # Atuin shell history
  eval "$(atuin init zsh --disable-up-arrow)"
fi
# Load Starship prompt
eval "$(starship init zsh)"
# Launch neofetch only in interactive shells and not within yazi
if [[ -n "$PS1" && -z "$YAZI_LEVEL" ]]; then
    clear && fastfetch
fi
