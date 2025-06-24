# ~/.config/fish/functions/ff.fish
function ff -d "Frecent file selector"
    if test (count $argv) -eq 0
        frecent --files --interactive
    else
        # Filter frecent files by the provided search term
        frecent --files 2>/dev/null | grep -i (string join '.*' $argv)
    end
end