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
# Enable menu selection for completions
zstyle ':completion:*' menu select
fpath=(${ASDF_DATA_DIR:-$HOME/.asdf}/completions $fpath) # append asdf completions to fpath
autoload -Uz compinit && compinit # initialise completions with ZSH's compinit

# Deactivate hx command completions
compdef -d hx
# Use fasd for hx command completions
zstyle ':completion:*:*:hx:*' command 'fasd --complete'

# #################################
# # Autocompletion priority
# #################################

# Activate fasd (easy file and dir jump)
eval "$(fasd --init auto)"

# #################################
# # Sourcing
# #################################

# Path setting
source ~/.config/zsh/.zsh_path
# Hooks
source ~/.config/zsh/.zsh_hooks
# Aliases
source ~/.config/zsh/.zsh_aliases
# Theme
source ~/.config/zsh/plugins/powerlevel10k/powerlevel10k.zsh-theme
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
[[ ! -f ~/.config/zsh/.p10k.zsh ]] || source ~/.config/zsh/.p10k.zsh


# #################################
# # Keybindings
# #################################

source ~/.config/zsh/zsh_keybinds.zsh

# #################################
# # Miscellaneous Configurations
# #################################

# Auto Notify
AUTO_NOTIFY_IGNORE+=("lf" "hugo serve" "rofi")
# Suggestion Strategy
ZSH_AUTOSUGGEST_STRATEGY=(match_prev_cmd history)
ZSH_AUTOSUGGEST_USE_ASYNC=1
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE="fg=#89b4fa"

# FZF Tab Config
source ~/.config/fzf-tab/fzf-tab.zsh


# #################################
# # App Specific Commands
# #################################

# Thefuck
eval "$(thefuck --alias fuck)"
# Hass cli
eval "$(_HASS_CLI_COMPLETE=source_zsh hass-cli)"
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

# Load Google Cloud SDK
if [ -f '/home/rash/builds/google-cloud-sdk/path.zsh.inc' ]; then
    source '/home/rash/builds/google-cloud-sdk/path.zsh.inc'
fi

# Load Google Cloud SDK completion with proper initialization
if [ -f '/home/rash/builds/google-cloud-sdk/completion.zsh.inc' ]; then
    # Load Google Cloud SDK completion
    source '/home/rash/builds/google-cloud-sdk/completion.zsh.inc'
fi

# Detect if shell is being launched from inside yazi
if [[ "$PPID" -eq "$(pgrep -o yazi)" ]]; then
    export IN_YAZI=1
fi

# Activate walk file manager
function lk {
  cd "$(walk --icons --with-border "$@")"
}

# Launch neofetch only in interactive shells and not within yazi
if [[ -n "$PS1" && -z "$IN_YAZI" ]]; then
    neofetch
fi
