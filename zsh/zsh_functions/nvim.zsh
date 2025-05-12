# Common implementation function
_nvim_wrapper() {
  if [ -d "$1" ]; then
    command nvim "$1" -c "Telescope find_files"
  else
    command nvim "$@"
  fi
}

# Define both nvim and nv using the common implementation
nvim() {
  _nvim_wrapper "$@"
}

nv() {
  _nvim_wrapper "$@"
}

# Open the cwd in nvim with Telescope file_browser
nvfb() {
  command nvim -c "Telescope file_browser"
}

