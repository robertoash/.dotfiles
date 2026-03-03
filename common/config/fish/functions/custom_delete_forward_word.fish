function custom_delete_forward_word
    set -l cmd (commandline)
    set -l pos (commandline -C)
    set -l len (string length -- "$cmd")

    if test $pos -ge $len
        return
    end

    set -l before (string sub -l $pos -- "$cmd")
    set -l after (string sub -s (math $pos + 1) -- "$cmd")
    set -l script (status dirname)/_word_boundary.py

    set -l result (python3 "$script" forward "$before" "$after")
    commandline -r -- "$result[2]"
    commandline -C "$result[1]"
end
