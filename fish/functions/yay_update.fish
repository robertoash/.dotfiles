function yay_update
    # Store initial package list
    set before (mktemp)
    pacman -Q > $before

    # Run the update
    yay -Syu --devel --noconfirm

    # Store final package list
    set after (mktemp)
    pacman -Q > $after

    # Create frame
    set width 96
    echo -e "\n"(string repeat -n $width '#')

    # Compare and show differences
    if not diff -q $before $after > /dev/null
        set title "=== Updated Packages ==="
        set padding (math "($width - "(string length $title)") / 2")
        printf "%*s%s\n" $padding "" $title
        echo
        diff $before $after | grep '^>' | sed 's/^> //' | while IFS= read -r package
            echo "  $package"
        end
    else
        set title "No updates available."
        set padding (math "($width - "(string length $title)") / 2")
        printf "%*s%s\n" $padding "" $title
    end

    # Close frame
    echo
    echo (string repeat -n $width '#')

    # Cleanup
    rm $before $after

    # Backup packages
    /home/rash/.config/scripts/backup/bkup_packages.py
end
