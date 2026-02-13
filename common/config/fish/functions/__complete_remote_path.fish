function __complete_remote_path
    # Called when __completion_get_type returns "remote"
    # Parses host:path from current token, executes remote ls, presents via fzf
    #
    # Supports formats:
    #   host:/path       (simple hostname)
    #   user@host:/path  (with username)
    #   alias:/path      (SSH config alias)

    set -l token (commandline -t)

    # Parse host and path from token
    if not string match -qr '^([^:]+):(.*)$' -- "$token"
        return 1
    end

    set -l remote_target $match[1]
    set -l remote_path $match[2]

    # Determine the directory to list
    set -l list_path "$remote_path"
    if test -z "$list_path"
        set list_path "."
    end

    # If path ends with something that's not a slash, it might be a partial name
    # Extract the directory prefix for ls and the partial name for fzf query
    set -l fzf_query ""
    if test -n "$remote_path"; and not string match -q '*/' -- "$remote_path"
        # Has a partial filename - split into dir + partial
        set -l dir_part (string replace -r '[^/]*$' '' -- "$remote_path")
        set fzf_query (string replace -r '.*/' '' -- "$remote_path")
        if test -n "$dir_part"
            set list_path "$dir_part"
        else
            set list_path "."
        end
    end

    # Execute remote ls with safety flags:
    # - BatchMode=yes: never prompt for password (silently fail)
    # - ConnectTimeout=2: don't hang for unreachable hosts
    # - StrictHostKeyChecking=accept-new: accept new host keys (don't prompt)
    # - LogLevel=ERROR: suppress warnings
    # - ls -1Ap: one per line, append / to dirs, show hidden (except . and ..)
    set -l results (ssh \
        -o "BatchMode=yes" \
        -o "ConnectTimeout=2" \
        -o "StrictHostKeyChecking=accept-new" \
        -o "LogLevel=ERROR" \
        "$remote_target" \
        "command ls -1Ap '$list_path' 2>/dev/null" 2>/dev/null)

    if test $status -ne 0; or test -z "$results"
        # SSH failed (unreachable, auth required, etc.) - fail silently
        commandline -f repaint
        return 1
    end

    # Prefix results with the directory path (so fzf shows full remote paths)
    set -l prefixed_results
    for result in $results
        if test "$list_path" = "."
            set -a prefixed_results "$result"
        else
            set -a prefixed_results "$list_path$result"
        end
    end

    # Present via fzf
    set -l selected (printf '%s\n' $prefixed_results | \
        command fzf \
            --height 40% \
            --reverse \
            --query "$fzf_query" \
            --header "Remote: $remote_target" \
            --color 'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff')

    if test -n "$selected"
        # Insert as host:selected_path
        # Escape spaces in the path for local shell
        set selected (string replace -a ' ' '\\ ' -- "$selected")
        commandline -t -- "$remote_target:$selected"
    end

    commandline -f repaint
end
