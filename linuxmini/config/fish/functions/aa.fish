# ~/.config/fish/functions/aa.fish
function aa -d "Frecent all items selector"
    if test (count $argv) -eq 0
        frecent --all --interactive
    else
        # Filter all frecent items by the provided search term
        frecent --all 2>/dev/null | grep -i (string join '.*' $argv)
    end
end