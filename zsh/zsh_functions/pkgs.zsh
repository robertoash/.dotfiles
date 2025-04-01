yayupdate() {
    # Store initial package list
    before=$(mktemp)
    pacman -Q > "$before"

    # Run the update
    yay -Syu --devel --noconfirm

    # Store final package list
    after=$(mktemp)
    pacman -Q > "$after"

    # Create frame
    width=96
    echo -e "\n$(printf '#%.0s' $(seq 1 $width))"

    # Compare and show differences
    if ! diff -q "$before" "$after" > /dev/null; then
        title="=== Updated Packages ==="
        padding=$(( (width - ${#title}) / 2 ))
        printf "%*s%s\n" $padding "" "$title"
        echo
        diff "$before" "$after" | grep '^>' | sed 's/^> //' | while IFS= read -r package; do
            echo "  $package"
        done
    else
        title="No updates available."
        padding=$(( (width - ${#title}) / 2 ))
        printf "%*s%s\n" $padding "" "$title"
    fi

    # Close frame
    echo
    echo "$(printf '#%.0s' $(seq 1 $width))"

    # Cleanup
    rm "$before" "$after"
}
