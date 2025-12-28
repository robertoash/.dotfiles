function hypr-update --description "Update all Hyprland-related packages"
    # Main Hyprland applications
    set main_apps \
        hyprland-git \
        hypridle-git \
        hyprlock-git \
        hyprpaper-git

    # Extended tools and utilities
    set extended_tools \
        hyprland-guiutils-git \
        pyprland-git \
        hyprlock-git

    # Hyprland libraries and protocols
    set libraries \
        hyprcursor-git \
        hyprgraphics-git \
        hyprland-protocols-git \
        hyprlang-git \
        hyprtoolkit-git \
        hyprutils-git \
        hyprwayland-scanner-git \
        hyprwire-git \
        xdg-desktop-portal-hyprland-git

    # Desktop portal
    set portal xdg-desktop-portal-hyprland-git

    # Combine all packages
    set all_packages $main_apps $extended_tools $libraries $portal

    echo "🔄 Updating Hyprland-related packages..."
    echo ""
    echo "📦 Main apps: $main_apps"
    echo "🔧 Extended tools: $extended_tools"
    echo "📚 Libraries: $libraries"
    echo "🔌 Portal: $portal"
    echo ""

    # Check if --confirm flag is present
    set -l confirm_mode no
    set -l filtered_args
    for arg in $argv
        if test "$arg" = "--confirm"
            set confirm_mode yes
        else
            set -a filtered_args $arg
        end
    end

    # --devel checks git repos for new commits
    # Note: May rebuild some packages even if unchanged, but ensures all updates are caught
    # Runs with --noconfirm by default unless --confirm is passed
    if test "$confirm_mode" = no
        yay -S --devel --noconfirm $filtered_args $all_packages
    else
        yay -S --devel $filtered_args $all_packages
    end

    if test $status -eq 0
        echo ""
        echo "✅ Hyprland packages updated successfully!"
    else
        echo ""
        echo "❌ Update failed with exit code $status"
        return $status
    end
end
