# Smart context-aware Tab completion with fzf
# Detects command context and launches appropriate fzf picker

function __smart_tab_complete
    set -l cmd (commandline -b)
    set -l token (commandline -t)
    set -l cursor_pos (commandline -C)

    # Extract path prefix and search base for relative/absolute paths
    set -l search_dir "."
    set -l path_prefix ""
    set -l query_part "$token"

    if string match -q -r '/' -- "$token"
        # Token contains a path - extract directory portion
        set path_prefix (string replace -r '[^/]*$' '' -- "$token")
        set query_part (string replace -r '.*/' '' -- "$token")
        if test -n "$path_prefix"; and test -d "$path_prefix"
            set search_dir "$path_prefix"
        end
    end

    # === TRIGGER WORDS (existing functionality) ===
    # fd triggers: fff, fdd, faa
    if string match -q -r '^f(ff|dd|aa)$' -- "$token"
        __fd_unified_widget
        return
    end

    # frecent triggers: ff, dd, aa
    switch "$token"
        case ff
            set -l result (frecent --files --interactive 2>/dev/null)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
        case dd
            set -l result (frecent --dirs --interactive 2>/dev/null)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
        case aa
            set -l result (frecent --all --interactive 2>/dev/null)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
    end

    # === SMART CONTEXT DETECTION ===
    # Get the command (first token) and check if we're in argument position
    set -l tokens (string split ' ' -- $cmd)
    set -l base_cmd $tokens[1]

    # Handle empty command line
    if test -z "$base_cmd"
        commandline -f complete
        return
    end

    # Strip any path prefix to get just the command name
    set base_cmd (basename $base_cmd)

    # Handle sudo/doas/env - get the actual command
    if contains $base_cmd sudo doas env nohup nice time watch strace ltrace
        if test (count $tokens) -ge 2
            set base_cmd (basename $tokens[2])
        else
            commandline -f complete
            return
        end
    end

    # Only trigger smart completion if we're after the command (have typed space)
    # and the token is empty or a partial path
    if test (count $tokens) -lt 2; and test -z "$token"
        commandline -f complete
        return
    end

    # === COMMAND CATEGORIES ===

    # Commands that ONLY want directories
    set -l dir_commands \
        cd z pushd popd \
        mkdir rmdir \
        ls ll lll lls llr llrl eza exa tree \
        yazi yz ranger nnn lf mc vifm broot br \
        j jump autojump fasd

    # Commands that ONLY want files
    set -l file_commands \
        vim nvim vi nano emacs micro helix hx kak \
        cat bat batcat less more head tail view \
        rm shred \
        touch \
        python python3 python2 py node ruby perl php lua luajit \
        bash sh zsh fish source \
        chmod chown chgrp \
        gzip gunzip bzip2 bunzip2 xz unxz zstd unzstd lz4 unlz4 \
        file stat wc md5sum sha256sum sha1sum sha512sum b2sum \
        diff vimdiff colordiff delta \
        mpv vlc mplayer ffplay ffmpeg ffprobe \
        feh imv sxiv nsxiv swayimg viu chafa \
        zathura evince okular mupdf xdg-open \
        patch \
        strip objdump nm readelf \
        pandoc \
        prettier eslint tsc tsx ts-node \
        rustfmt cargo-fmt \
        black isort flake8 mypy pylint ruff \
        shfmt shellcheck \
        jq yq fx gron \
        sqlite3 \
        gpg gpg2 \
        scp \
        split csplit \
        sort uniq cut paste join \
        awk sed \
        hexdump xxd od \
        strings \
        pdftotext pdfimages pdfinfo \
        identify convert mogrify magick \
        exiftool mediainfo \
        transmission-remote-cli aria2c wget curl \
        xclip xsel wl-copy pbcopy

    # Commands that want both files AND directories
    set -l both_commands \
        cp mv rsync rclone \
        ln \
        code code-insiders subl sublime atom \
        tar zip unzip 7z 7za rar unrar \
        fd find rg grep ug ugrep ag ack \
        du ncdu dust gdu dua \
        open xdg-open dolphin nautilus thunar pcmanfm \
        trash trash-put del gio \
        chattr lsattr \
        zip unzip \
        scp rsync \
        realpath readlink \
        basename dirname

    # Git subcommands that want files
    set -l git_file_subcommands add checkout restore diff rm mv log show blame annotate

    # Determine completion type
    set -l completion_type "default"

    # Special handling for git
    if test "$base_cmd" = "git"; and test (count $tokens) -ge 2
        set -l git_subcmd $tokens[2]
        if contains $git_subcmd $git_file_subcommands
            set completion_type "both"
        end
    else if contains $base_cmd $dir_commands
        set completion_type "dirs"
    else if contains $base_cmd $file_commands
        set completion_type "files"
    else if contains $base_cmd $both_commands
        set completion_type "both"
    end

    # === LAUNCH APPROPRIATE FZF ===
    # fd behavior differs for relative vs absolute paths:
    # - Relative paths (../): fd outputs with prefix (../file) - don't prepend
    # - Absolute paths (~/, /tmp/): fd outputs without prefix (file) - prepend needed
    switch $completion_type
        case dirs
            set -l result (begin; fd -Hi --no-ignore-vcs -t d --max-depth 1 . "$search_dir"; fd -Hi --no-ignore-vcs -t d --min-depth 2 . "$search_dir"; end | fzf --height 40% --reverse --query "$query_part")
            if test -n "$result"
                # Prepend path_prefix only for absolute paths (starting with / or ~)
                if string match -q -r '^[/~]' -- "$path_prefix"
                    commandline -t -- (string escape "$path_prefix$result")
                else
                    commandline -t -- (string escape "$result")
                end
            end
            commandline -f repaint

        case files
            set -l result (begin; fd -Hi --no-ignore-vcs -t f --max-depth 1 . "$search_dir"; fd -Hi --no-ignore-vcs -t f --min-depth 2 . "$search_dir"; end | fzf --height 40% --reverse --query "$query_part")
            if test -n "$result"
                # Prepend path_prefix only for absolute paths (starting with / or ~)
                if string match -q -r '^[/~]' -- "$path_prefix"
                    commandline -t -- (string escape "$path_prefix$result")
                else
                    commandline -t -- (string escape "$result")
                end
            end
            commandline -f repaint

        case both
            set -l result (begin; fd -Hi --no-ignore-vcs --max-depth 1 . "$search_dir"; fd -Hi --no-ignore-vcs --min-depth 2 . "$search_dir"; end | fzf --height 40% --reverse --query "$query_part")
            if test -n "$result"
                # Prepend path_prefix only for absolute paths (starting with / or ~)
                if string match -q -r '^[/~]' -- "$path_prefix"
                    commandline -t -- (string escape "$path_prefix$result")
                else
                    commandline -t -- (string escape "$result")
                end
            end
            commandline -f repaint

        case '*'
            # Fall back to fish's default completion
            commandline -f complete
    end
end
