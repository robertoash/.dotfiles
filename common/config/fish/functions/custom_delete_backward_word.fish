function custom_delete_backward_word
    set -l cmd (commandline)
    set -l pos (commandline -C)

    if test $pos -eq 0
        return
    end

    set -l before (string sub -l $pos -- "$cmd")
    set -l after (string sub -s (math $pos + 1) -- "$cmd")
    set -l script (status dirname)/_word_boundary.py

    set -l result (python3 "$script" back "$before" "$after")
    commandline -r -- "$result[2]"
    commandline -C "$result[1]"
end
