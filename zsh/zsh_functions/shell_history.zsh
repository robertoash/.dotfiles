# Stop shell history recording
stp_history() {
  zshaddhistory() {
    return 1
  }

  # Redirect _Z_DATA to /dev/null to prevent z from creating a new .z file
  export _Z_DATA=/dev/null

  # Silencing permission denied errors from z plugin
  unalias zshz 2>/dev/null || true
  function zshz { command zshz "$@" 2>/dev/null; }

  echo 'History recording stopped.'
}

# Start shell history recording
strt_history() {
  unset -f zshaddhistory

  # Set _Z_DATA to enable z to update its database again
  export _Z_DATA=~/.config/z/.z

  # Restore original z command
  unfunction zshz 2>/dev/null || true
  source ~/.config/zsh/plugins/zsh-z/zsh-z.plugin.zsh

  echo 'History recording started.'
}
