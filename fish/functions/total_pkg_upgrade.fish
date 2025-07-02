function total_pkg_upgrade
    # Store initial package list
    set before (mktemp)
    /home/rash/.config/scripts/backup/bkup_packages.py -s $before > /dev/null
    sort -o $before $before

    # Run the updates
    echo "==> Updating all packages..."

    if command -v yay > /dev/null
        echo "--> Updating pacman/yay packages..."
        yay -Syu --devel --noconfirm
    else
        echo "--> yay not found, skipping pacman/yay updates."
    end

    if command -v pipx > /dev/null
        echo "--> Updating pipx packages..."
        pipx upgrade-all
    else
        echo "--> pipx not found, skipping pipx updates."
    end

    if command -v ya > /dev/null
        echo "--> Updating yazi packages..."
        ya pkg upgrade
    else
        echo "--> yazi (ya) not found, skipping yazi updates."
    end

    if command -v cargo-install-update > /dev/null
        echo "--> Updating cargo packages..."
        cargo install-update -a
    else
        echo "--> cargo-install-update not found, skipping cargo updates."
        echo "    (Hint: cargo install cargo-update)"
    end

    if command -v npm > /dev/null
        echo "--> Updating npm packages..."
        npm update -g
    else
        echo "--> npm not found, skipping npm updates."
    end

    echo "==> Updates finished."

    # Store final package list
    set after (mktemp)
    /home/rash/.config/scripts/backup/bkup_packages.py -s $after > /dev/null
    sort -o $after $after

    # Create frame
    set width 96
    echo -e "
"(string repeat -n $width '#')

    # Compare and show differences
    if not diff -q $before $after > /dev/null
        set title "=== Upgraded Packages ==="
        set padding (math --scale=0 "($width - "(string length $title)") / 2")
        printf "%*s%s
" $padding "" $title
        echo

        comm -13 $before $after | sed 's/###/ /g' | sed 's/^/  /'

    else
        set title "No updates available."
        set padding (math --scale=0 "($width - "(string length $title)") / 2")
        printf "%*s%s
" $padding "" $title
    end

    # Close frame
    echo
    echo (string repeat -n $width '#')

    # Cleanup
    rm $before $after

    # Backup packages
    echo "--> Backing up new package list..."
    /home/rash/.config/scripts/backup/bkup_packages.py
end