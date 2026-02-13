# Command categorization config and context detection for smart completion
# Provides command categorization data and __completion_get_type function

# === COMMAND CATEGORIZATION DATA ===

# Commands that ONLY want directories
set -g __cc_dir_cmds \
    cd z pushd popd \
    mkdir rmdir \
    ls ll lll lls llr llrl eza exa tree \
    yazi yz ranger nnn lf mc vifm broot br \
    j jump autojump fasd \
    sshfs dust

# Commands that ONLY want files
set -g __cc_file_cmds \
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
    split csplit \
    sort uniq cut paste join \
    awk sed \
    hexdump xxd od \
    strings \
    pdftotext pdfimages pdfinfo \
    identify convert mogrify magick \
    exiftool mediainfo \
    transmission-remote-cli aria2c wget curl \
    xclip xsel wl-copy pbcopy \
    eog gimp inkscape libreoffice soffice ansible-playbook terraform terragrunt

# Commands that want both files AND directories
set -g __cc_both_cmds \
    cp mv rsync rclone \
    ln \
    code code-insiders subl sublime atom \
    tar zip unzip 7z 7za rar \
    fd find rg grep ug ugrep ag ack \
    du ncdu dust gdu dua \
    open xdg-open dolphin nautilus thunar pcmanfm \
    trash trash-put del gio \
    chattr lsattr \
    scp \
    realpath readlink \
    basename dirname \
    unrar atool codium

# Git subcommands that want files/both
set -g __cc_git_file_subcmds add checkout restore diff rm mv log show blame annotate stash

# Commands where fish native completions are richer than fzf (flag-heavy commands)
set -g __cc_native_cmds \
    git docker kubectl systemctl pacman yay paru pip cargo npm yarn brew apt dnf

# Wrapper commands to strip before categorization
set -g __cc_wrapper_cmds sudo doas env nohup nice time watch strace ltrace

# === CONTEXT DETECTION FUNCTION ===

function __completion_get_type
    # Returns one of: dirs, files, both, native, remote, trigger:ff, trigger:dd, trigger:aa, trigger:fff, trigger:fdd, trigger:faa

    set -l cmd (commandline -b)
    set -l token (commandline -t)
    set -l tokens (commandline -opc)  # Use fish's proper tokenizer (handles quoting)

    # Handle trigger words FIRST (before any other logic)
    switch "$token"
        case ff
            echo "trigger:ff"
            return
        case dd
            echo "trigger:dd"
            return
        case aa
            echo "trigger:aa"
            return
        case fff
            echo "trigger:fff"
            return
        case fdd
            echo "trigger:fdd"
            return
        case faa
            echo "trigger:faa"
            return
    end

    # Empty command line -> native completion
    if test (count $tokens) -eq 0
        echo "native"
        return
    end

    # Extract base command, stripping wrappers
    set -l base_cmd (basename -- $tokens[1])
    if contains $base_cmd $__cc_wrapper_cmds
        if test (count $tokens) -ge 2
            set base_cmd (basename -- $tokens[2])
        else
            echo "native"
            return
        end
    end

    # If we're still on the command itself (no space after it), use native
    if test (count $tokens) -lt 2; and test -z "$token"
        echo "native"
        return
    end

    # Special: git subcommand detection
    if test "$base_cmd" = git; and test (count $tokens) -ge 2
        if contains $tokens[2] $__cc_git_file_subcmds
            echo "both"
            return
        end
        echo "native"
        return
    end

    # Special: remote path detection (host:path pattern)
    if string match -q '*:*' -- "$token"
        # Only if a remote-capable command
        if contains $base_cmd scp rsync ssh sftp
            echo "remote"
            return
        end
    end

    # Categorize by command lists
    if contains $base_cmd $__cc_native_cmds
        echo "native"
    else if contains $base_cmd $__cc_dir_cmds
        echo "dirs"
    else if contains $base_cmd $__cc_file_cmds
        echo "files"
    else if contains $base_cmd $__cc_both_cmds
        echo "both"
    else
        # Unknown command: check xdg-mime as a fallback
        # If the command is a registered MIME handler, it's likely a file opener
        if command -q xdg-mime
            set -l cmd_path (command -s $base_cmd 2>/dev/null)
            if test -n "$cmd_path"; and test -f /usr/share/applications/$base_cmd.desktop
                echo "files"
                return
            end
        end
        # Final default: "both" (files + dirs is safest)
        echo "both"
    end
end
