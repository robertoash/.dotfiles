# ~/.config/fish/conf.d/00_nix.fish
# Nix and Home Manager Environment

# Add Nix paths to fish
if test -d ~/.nix-profile/share/fish/vendor_functions.d
    set -gp fish_function_path ~/.nix-profile/share/fish/vendor_functions.d
end

# Add Nix bin to PATH first
if test -d ~/.nix-profile/bin
    fish_add_path --prepend ~/.nix-profile/bin
end

# Source Nix and home-manager environment variables
if test -f ~/.nix-profile/etc/profile.d/hm-session-vars.sh
    # Use fenv to source bash script in fish (fenv is now available from vendor_functions.d)
    fenv source ~/.nix-profile/etc/profile.d/hm-session-vars.sh
end
