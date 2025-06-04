# Common implementation function
function nv
    command nvim $argv
end

# Open the cwd in nvim with Telescope file_browser
function nvfb
    command nvim -c "Telescope file_browser"
end