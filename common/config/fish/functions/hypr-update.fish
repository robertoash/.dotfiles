function hypr-update --description "Update all Hyprland-related packages"
    # Main Hyprland applications
    set main_apps \
        hyprland-git \
        hypridle \
        hyprlock-git \
        hyprpaper-git

    # Extended tools and utilities
    set extended_tools \
        hyprland-guiutils-git \
        pyprland-git

    # Hyprland libraries and protocols
    set libraries \
        hyprcursor-git \
        hyprgraphics-git \
        hyprland-protocols-git \
        hyprlang-git \
        hyprtoolkit-git \
        hyprutils-git \
        hyprwayland-scanner-git \
        hyprwire-git

    # Desktop portal
    set portal xdg-desktop-portal-hyprland

    # Combine all packages
    set all_packages $main_apps $extended_tools $libraries $portal

    echo "🔄 Updating Hyprland-related packages..."
    echo ""
    echo "📦 Main apps: $main_apps"
    echo "🔧 Extended tools: $extended_tools"
    echo "📚 Libraries: $libraries"
    echo "🔌 Portal: $portal"
    echo ""

    yay -S --needed --devel $all_packages

    if test $status -eq 0
        echo ""
        echo "✅ Hyprland packages updated successfully!"
    else
        echo ""
        echo "❌ Update failed with exit code $status"
        return $status
    end
end
