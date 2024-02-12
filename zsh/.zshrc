
# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.config/zsh/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi


# #################################
# # History & Cache
# #################################

HISTSIZE=10000
SAVEHIST=10000
HISTFILE=~/.config/zsh/.zsh_history


# #################################
# # Environment Variables
# #################################

# Plain
export EDITOR="nano"
export TERMINAL="alacritty"
export _Z_DATA=~/.config/z/.z
export GTK2_RC_FILES="$HOME/.config/gtk-2.0/gtkrc-2.0"
export YARN_RC_FILENAME=~/.config/yarn/.yarnrc
# Secrets
eval $(.config/scripts/shell/secure_env_secrets.py)


# #################################
# # Aliases
# #################################

# Shell aliases
[ -f "${XDG_CONFIG_HOME}/shell/aliases" ] && source "${XDG_CONFIG_HOME}/shell/aliases"
# App aliases
alias ll="exa --all --color=always --icons --group-directories-first --git -Hah"
alias lll="ll -l -a"
alias lls="lll -s size"
alias llt="ll -T -L"
alias vim="vim -u ~/.config/vim/vimrc"
alias lf="lfcd"
alias delete_gone_branches="git branch -vv | awk '$0 ~ /: gone]/ {print $1;}' | xargs -r git branch -D"
alias xeyes="xprop"
alias "??"="gh copilot suggest -t shell "
alias "??g"="gh copilot suggest -t git "
alias "??gh"="gh copilot suggest -t gh "
alias "??x"="gh copilot explain "
alias "dsp"="bash ~/.config/scripts/docker/docker_simple.sh"
alias "drdp"="bash ~/.config/scripts/docker/docker_redeploy_container.sh"
alias "mcon"="mullvad connect"
alias "mdis"="mullvad disconnect"
alias "mst"="mullvad status"


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

# Custom
source ~/.config/zsh/.oda.zsh
# Theme
source ~/.config/zsh/powerlevel10k/powerlevel10k.zsh-theme
# Plugins
source ~/.config/zsh/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source ~/.config/zsh/zsh-autosuggestions/zsh-autosuggestions.zsh
source ~/.config/zsh/zsh-history-substring-search/zsh-history-substring-search.zsh
source ~/.config/zsh/zsh-z/zsh-z.plugin.zsh
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
