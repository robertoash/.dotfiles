# Stop shell history recording
stp_history() {
  function zshaddhistory() {
    return 1
  }
  echo 'History recording stopped.'
}

# Start shell history recording
strt_history() {
  unset -f zshaddhistory
  echo 'History recording started.'
}