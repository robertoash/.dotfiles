# Stop shell history recording
stp_history() {
  function zshaddhistory() {
    return 1
  }

  # Stop resh daemon
  resh-daemon-stop

  # Set an environment variable to disable resh hooks
  # Had to modify __resh_preexec and __resh_precmd
  # on ~/.resh/hooks.sh to check for this variable
  # and exit early if it is set.
  export RESH_HISTORY_DISABLED=1

  # Redirect _Z_DATA to /dev/null to prevent z from creating a new .z file
  export _Z_DATA=/dev/null

  echo 'History recording stopped.'
}

# Start shell history recording
strt_history() {
  unset -f zshaddhistory

  resh-daemon-start

  # Unset the environment variable
  unset RESH_HISTORY_DISABLED

  # Set _Z_DATA to enable z to update its database again
  export _Z_DATA=~/.config/z/.z

  echo 'History recording started.'
}