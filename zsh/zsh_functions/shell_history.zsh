# Stop shell history recording
stop_history() {
  HISTSIZE=0
  SAVEHIST=0
  echo "History recording stopped."
}

# Start shell history recording
start_history() {
  HISTSIZE=10000  # Adjust as desired
  SAVEHIST=10000  # Adjust as desired
  echo "History recording started."
}
