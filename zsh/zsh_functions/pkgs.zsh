yayupdate() {
    output=$(mktemp)
    yay -Syu --devel --noconfirm | tee "$output"

    echo -e "\n=== Updated Packages ==="

    # Extract all package update sections and concatenate
    packages=$(grep -A 1000 "Package (" "$output" | grep -E '^[a-zA-Z0-9_.+-]+ [0-9]' | column -t)

    if [[ -z "$packages" ]]; then
        echo "No packages were updated."
    else
        echo "$packages"

        # Extract Net Upgrade Size and sum it up
        total_size=$(grep -E "Net Upgrade Size:" "$output" | awk '{print $NF, $(NF-1)}' | tr ',' '.' | awk '
        {
            if ($2 == "MiB") sum+=$1;
            else if ($2 == "GiB") sum+=$1*1024;
        }
        END {printf "%.2f MiB\n", sum}')

        echo -e "\nTotal Net Upgrade Size: $total_size"
    fi

    # Dynamically find and list all failed installations
    if grep -q "Failed to install the following packages" "$output"; then
        echo -e "\n⚠️  Installation Errors Detected: ⚠️"
        awk '/Failed to install the following packages/,0' "$output" | tail -n +2
    fi

    rm "$output"
}
