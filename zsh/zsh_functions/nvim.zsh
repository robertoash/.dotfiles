nv() {
  if [ -d "$1" ]; then
    nvim -c "cd $(printf '%q' "$1")"
  else
    nvim "$@"
  fi
}

