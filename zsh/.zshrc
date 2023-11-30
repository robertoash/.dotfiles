
# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.config/zsh/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# History in cache directory:
HISTSIZE=10000
SAVEHIST=10000
HISTFILE=~/.config/zsh/.zsh_history

# aliases
[ -f "${XDG_CONFIG_HOME}/shell/aliases" ] && source "${XDG_CONFIG_HOME}/shell/aliases"
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
alias "dsp"="bash ~/.config/scripts/docker_simple.sh"
alias drdp="bash ~/.config/scripts/docker_redeploy_container.sh "

# options
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

# keybinds
source ~/.config/zsh/keybinds.zsh

# theme/plugins
#source ~/.config/lf/lfcd.sh
#source ~/.config/zsh/zsh-auto-notify/auto-notify.plugin.zsh
#source ~/.config/zsh/you-should-use/you-should-use.plugin.zsh
source ~/.config/zsh/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source ~/.config/zsh/zsh-autosuggestions/zsh-autosuggestions.zsh
source ~/.config/zsh/zsh-history-substring-search/zsh-history-substring-search.zsh
source ~/.config/zsh/zsh-z/zsh-z.plugin.zsh

autoload -U compinit; compinit
zstyle ':completion:*' menu select

# history substring search options
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down

# auto notify options
AUTO_NOTIFY_IGNORE+=("lf" "hugo serve" "rofi")

ZSH_AUTOSUGGEST_STRATEGY=(history completion)

source ~/.config/zsh/powerlevel10k/powerlevel10k.zsh-theme

# To customize prompt, run `p10k configure` or edit ~/.config/zsh/.p10k.zsh.
[[ ! -f ~/.config/zsh/.p10k.zsh ]] || source ~/.config/zsh/.p10k.zsh

# Run neofetch
neofetch

# The fuck
eval $(thefuck --alias fuck)

# Use pyenv
eval "$(pyenv init -)"

# Enable resh
[[ -f ~/.resh/shellrc ]] && source ~/.resh/shellrc

# Change vimrc location
#export VIMINIT='source $MYVIMRC'
#export MYVIMRC='~/.config/vim/vimrc'

# Set cwd on lf exit
LFCD="/home/rash/.config/lf/lfcd.sh"                    # pre-built binary, make sure to use absolute path
if [ -f "$LFCD" ]; then
    source "$LFCD"
fi
bindkey -s '^o' 'lfcd\n'
