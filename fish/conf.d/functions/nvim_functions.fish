# Common implementation function
function nvim
    command nvim $argv
    for f in $argv
        if test -f "$f"; and test "$SECURE_SHELL" != "1"
            fre --add "$f"
        end
    end
end

function nv
    nvim $argv
end 

# Open the cwd in nvim with Telescope file_browser
function nvfb
    command nvim -c "Telescope file_browser"
end
