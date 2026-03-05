function accept_next_path_segment
    if not commandline --showing-suggestion
        return
    end

    set -l pos (commandline --cursor)
    set -l buffer (commandline)

    # Accept the full suggestion to read its text, then reset
    commandline -f accept-autosuggestion
    set -l suggestion (string sub --start (math $pos + 1) -- (commandline))
    commandline -- "$buffer"
    commandline -C $pos

    if test -z "$suggestion"
        return
    end

    set -l n (python3 (status dirname)/_word_boundary.py accept "" "$suggestion")

    for i in (seq $n)
        commandline -f forward-single-char
    end
end
