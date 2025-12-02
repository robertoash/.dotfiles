# ~/.config/fish/functions/dd.fish
function dd -d "Frecent directory selector"
    if test (count $argv) -eq 0
        frecent --dirs --interactive
    else
        # Filter frecent directories by the provided search term
        frecent --dirs 2>/dev/null | grep -i (string join '.*' $argv)
    end
end