# Create the headless output
hyprctl output create headless iPadScreen
hyprctl keyword monitor iPadScreen,1280x960@60,6000x2840,1
sleep 0.5

# Get the output ID and update sunshine.conf
set output_id (hyprctl monitors -j | jq -r '.[] | select(.name=="iPadScreen") | .id')
sed -i "s/^output_name = .*/output_name = $output_id/" ~/.config/sunshine/sunshine.conf

# Setup cleanup function
function cleanup
    echo "Cleaning up iPadScreen output..."
    hyprctl output remove iPadScreen
    sed -i "s/^output_name = .*/output_name = 0/" ~/.config/sunshine/sunshine.conf
end

# Setup signal traps
trap cleanup SIGINT SIGTERM

# Start sunshine in foreground and wait for it
sunshine

# Run cleanup after sunshine exits
cleanup
