# Load all startup functions from subdirectory
for file in ~/.config/fish/conf.d/startup_functions/*.fish
    source $file
end
