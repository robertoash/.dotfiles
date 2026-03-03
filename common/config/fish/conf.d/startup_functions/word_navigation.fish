# Custom word navigation (cursor movement only)
# Delete functions are in ~/.config/fish/functions/custom_delete_*.fish

function _find_left_boundaries
    set -l cmdline (commandline)
    set -l len (string length -- "$cmdline")
    set -l boundaries 0

    for i in (seq 1 $len)
        set -l char (string sub --start $i --length 1 -- "$cmdline")

        if test "$char" = " "
            set boundaries $boundaries (math $i - 1) $i
        else if test "$char" = "/"
            set boundaries $boundaries $i
        end
    end

    set boundaries $boundaries $len
    printf '%s\n' $boundaries | sort -n | uniq
end

function _find_right_boundaries
    set -l cmdline (commandline)
    set -l len (string length -- "$cmdline")
    set -l boundaries 0

    for i in (seq 1 $len)
        set -l char (string sub --start $i --length 1 -- "$cmdline")

        if test "$char" = " "
            set boundaries $boundaries (math $i - 1) $i
        else if test "$char" = "/"
            set boundaries $boundaries (math $i - 1)
        end
    end

    set boundaries $boundaries $len
    printf '%s\n' $boundaries | sort -n | uniq
end

function custom_backward_word
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_left_boundaries)

    set -l prev_boundary -1

    for boundary in $boundaries
        if test $boundary -lt $current_pos
            set prev_boundary $boundary
        else
            break
        end
    end

    if test $prev_boundary -ge 0
        commandline --cursor $prev_boundary
    end
end

function custom_forward_word
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_right_boundaries)

    for boundary in $boundaries
        if test $boundary -gt $current_pos
            commandline --cursor $boundary
            return
        end
    end
end

function _find_left_space_boundaries
    set -l cmdline (commandline)
    set -l len (string length -- "$cmdline")
    set -l boundaries 0

    for i in (seq 1 $len)
        set -l char (string sub --start $i --length 1 -- "$cmdline")

        if test "$char" = " "
            set boundaries $boundaries (math $i - 1)
        end
    end

    set boundaries $boundaries $len
    printf '%s\n' $boundaries | sort -n | uniq
end

function _find_right_space_boundaries
    set -l cmdline (commandline)
    set -l len (string length -- "$cmdline")
    set -l boundaries 0

    for i in (seq 1 $len)
        set -l char (string sub --start $i --length 1 -- "$cmdline")

        if test "$char" = " "
            set boundaries $boundaries $i
        end
    end

    set boundaries $boundaries $len
    printf '%s\n' $boundaries | sort -n | uniq
end

function custom_backward_word_space
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_left_space_boundaries)

    set -l prev_boundary -1

    for boundary in $boundaries
        if test $boundary -lt $current_pos
            set prev_boundary $boundary
        else
            break
        end
    end

    if test $prev_boundary -ge 0
        commandline --cursor $prev_boundary
    end
end

function custom_forward_word_space
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_right_space_boundaries)

    for boundary in $boundaries
        if test $boundary -gt $current_pos
            commandline --cursor $boundary
            return
        end
    end
end
