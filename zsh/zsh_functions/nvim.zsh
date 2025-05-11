nv() {
  if [ -d "$1" ]; then
    nvim -c "cd $(printf '%q' "$1")" -c "Telescope file_browser hidden=true grouped=true"
  else
    nvim "$@"
  fi
}

# Open the cwd in nvim
nvd() {
  nvim -c "Telescope file_browser hidden=true grouped=true"
}

