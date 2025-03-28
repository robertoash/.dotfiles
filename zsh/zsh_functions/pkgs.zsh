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
        updated_packages=$(diff "$before" "$after" | grep '^>' | sed 's/^> //')

        # Show each updated package and its dependencies
        while IFS= read -r package; do
            pkg_name=$(echo "$package" | cut -d' ' -f1)
            pkg_version=$(echo "$package" | cut -d' ' -f2)
            echo "  $pkg_name ($pkg_version):"
            pactree -l --optional=1 "$pkg_name" | sed 's/^/  /'
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
