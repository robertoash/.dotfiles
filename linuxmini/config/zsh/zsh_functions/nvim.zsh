# Common implementation function
nv() {
    command nvim "$@"
}

# Open the cwd in nvim with Telescope file_browser
nvfb() {
  command nvim -c "Telescope file_browser"
}

