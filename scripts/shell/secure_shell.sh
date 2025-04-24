#!/bin/bash
export ZDOTDIR_PARENT=$(mktemp -d)
export ZDOTDIR="$ZDOTDIR_PARENT/zsh"
export HISTFILE=$(mktemp)
export SECURE_SHELL=1

# Copy your full config into the temp ZDOTDIR
cp -r ~/.config/zsh/ "$ZDOTDIR/"
#echo "ZDOTDIR=$ZDOTDIR/zsh" > "$ZDOTDIR/.zshenv"

# Mark this as a secure shell session for future conditional commands
touch "$ZDOTDIR/.secure_shell"

cleanup() {
    [[ "$ZDOTDIR_PARENT" == /tmp/* ]] && rm -rf "$ZDOTDIR_PARENT"
    [[ "$HISTFILE" == /tmp/* ]] && rm -f "$HISTFILE"
}

# Trap all common exits
trap cleanup EXIT HUP INT QUIT TERM

# Launch Zsh
zsh