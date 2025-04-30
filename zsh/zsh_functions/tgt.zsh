s_t() {
  local short_name="$1"
  shift

  if [[ -z "$short_name" || -z "$1" ]]; then
    echo "Usage: s_t <short_name> <message>"
    return 1
  fi

  local upper_name="${(U)short_name}"    # Normalize to uppercase
  local var_name="TGT_${upper_name}"
  local real_name="${(P)var_name}"

  if [[ -z "$real_name" ]]; then
    echo "❌ Unknown short name: $short_name"
    return 2
  fi

  # Reconstruct the full message from all remaining args
  local message="$*"

  # Auto-wrap the message in quotes only if it's not already quoted
  if [[ "$message" != \"*\" && "$message" != \'*\' ]]; then
    message="\"$message\""
  fi

  eval "tgt -s \"$real_name\" $message"
}
