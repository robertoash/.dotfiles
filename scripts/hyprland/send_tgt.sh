#!/usr/bin/env bash

# Source env file for TGT_* variables
ENV_FILE="$HOME/.config/zsh/sources/.zsh_secrets"

if [[ -f "$ENV_FILE" ]]; then
  source "$ENV_FILE"
else
  notify-send "❌ Missing env file" "$ENV_FILE"
  exit 1
fi

short_name="$1"
shift

if [[ -z "$short_name" || -z "$1" ]]; then
  notify-send "Usage" "send_tgt.sh <short_name> <message>"
  exit 1
fi

upper_name=$(echo "$short_name" | tr '[:lower:]' '[:upper:]')
var_name="TGT_${upper_name}"
real_name="${!var_name}"

if [[ -z "$real_name" ]]; then
  notify-send "❌ Unknown short name" "$short_name"
  exit 2
fi

# Reconstruct full message
message="$*"

# Wrap if not already quoted
if [[ ! "$message" =~ ^\".*\"$ && ! "$message" =~ ^\'.*\'$ ]]; then
  message="\"$message\""
fi

notify-send "TGT" "Sending to $real_name: $message"

# Use eval for proper quoting like Zsh version
eval "/home/rash/.cargo/bin/tgt -s \"$real_name\" $message"
