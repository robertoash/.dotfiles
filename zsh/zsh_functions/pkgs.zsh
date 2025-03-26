yayupdate() {
    # Store initial package list
    before=$(mktemp)
    yay -Qm > "$before"

    # Run the update
    yay -Syu --devel --noconfirm

    # Store final package list
    after=$(mktemp)
    yay -Qm > "$after"

    # Create frame
    width=80
    echo -e "\n$(printf '#%.0s' $(seq 1 $width))"

    # Compare and show differences
    if ! diff -q "$before" "$after" > /dev/null; then
        title="=== Updated Packages ==="
        padding=$(( (width - ${#title}) / 2 ))
        printf "%*s%s\n" $padding "" "$title"
        echo
        updated_packages=$(diff "$before" "$after" | grep '^>' | sed 's/^> //' | cut -d' ' -f1)

        # Show each updated package and its dependencies
        while IFS= read -r package; do
            echo "  $package:"
            pactree -l 1 "$package" | sed 's/^/  /'
        done <<< "$updated_packages"
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
