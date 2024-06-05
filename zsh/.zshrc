
# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.config/zsh/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi


# #################################
# # Path setting
# #################################

# Pipx path
export PATH="$PATH:/home/rash/.local/bin"

# Add sutff to python path
export PYTHONPATH="$PYTHONPATH:/home/rash/.config/scripts"


# #################################
# # History & Cache
# #################################

HISTSIZE=10000
SAVEHIST=10000
HISTCONTROL=ignoreboth
HISTFILE=~/.config/zsh/.zsh_history


# #################################
# # Environment Variables
# #################################

source ~/.config/zsh/.zsh_envs


# #################################
# # Options
# #################################

unsetopt menu_complete
unsetopt flowcontrol
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
autoload -U compinit; compinit
zstyle ':completion:*' menu select


# #################################
# # Sourcing
# #################################

# Aliases
source ~/.config/zsh/.zsh_aliases
# Theme
source ~/.config/zsh/plugins/powerlevel10k/powerlevel10k.zsh-theme
# Plugins
source ~/.config/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source ~/.config/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
source ~/.config/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh
source ~/.config/zsh/plugins/zsh-z/zsh-z.plugin.zsh
# Functions
source ~/.config/zsh/.zsh_functions
# Broot
source ~/.config/broot/launcher/bash/br
# Prompt Customization & Utilities
[[ ! -f ~/.config/zsh/.p10k.zsh ]] || source ~/.config/zsh/.p10k.zsh


# #################################
# # Keybindings
# #################################

source ~/.config/zsh/keybinds.zsh
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down
bindkey -s '^o' 'lfcd\n'


# #################################
# # Miscellaneous Configurations
# #################################

# Auto Notify
AUTO_NOTIFY_IGNORE+=("lf" "hugo serve" "rofi")
# Suggestion Strategy
ZSH_AUTOSUGGEST_STRATEGY=(history completion)


# #################################
# # App Specific Commands
# #################################

# Neofetch
neofetch
# Thefuck
eval $(thefuck --alias fuck)
# Resh
[[ -f ~/.resh/shellrc ]] && source ~/.resh/shellrc
# Hass cli
eval "$(_HASS_CLI_COMPLETE=source_zsh hass-cli)"
# LF (set cwd on exit)
LFCD="/home/rash/.config/lf/lfcd.sh"
if [ -f "$LFCD" ]; then
    source "$LFCD"
fi
# Hook direnv
eval "$(direnv hook zsh)"
# SGPT shell integration
_sgpt_zsh() {
if [[ -n "$BUFFER" ]]; then
    _sgpt_prev_cmd=$BUFFER
    BUFFER+="⌛"
    zle -I && zle redisplay
    BUFFER=$(sgpt --shell <<< "$_sgpt_prev_cmd" --no-interaction)
    zle end-of-line
fi
}
zle -N _sgpt_zsh
bindkey ^l _sgpt_zsh
