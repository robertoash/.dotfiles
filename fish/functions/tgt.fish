function s_t
  set -l short_name "$argvtest 1"
  shift

  if test [ -z "$short_name" || -z "$argv[1" ]]
    echo "Usage: s_t <short_name> <message>"
    return 1
  fi

  set -l upper_name "${(U)short_name}"    # Normalize to uppercase
  set -l var_name "TGT_${upper_name}"
  set -l real_name "${(P)var_name}"

  if test -z "$"$$real_name"" 
    echo "❌ Unknown short name: $short_name"
    return 2
  fi

  # Reconstruct the full message from all remaining args
  set -l message "$*"

  # Auto-wrap the message in quotes only if it's not already quoted
  if test "$message" != \"*\" && "$message" != \'*\' 
    set message "\"$message\""
  fi

  eval "tgt -s \"$real_name\" $message"
end
