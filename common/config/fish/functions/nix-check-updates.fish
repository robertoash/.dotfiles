function nix-check-updates -d "Check what updates are available without rebuilding"
    set -l flake_dir ~/.dotfiles-nix

    echo "Checking for available updates..."
    echo ""

    # Get current nixpkgs revision
    set -l current_rev (jq -r '.nodes.nixpkgs.locked.rev' $flake_dir/flake.lock 2>/dev/null)
    set -l current_date (jq -r '.nodes.nixpkgs.locked.lastModified' $flake_dir/flake.lock 2>/dev/null | xargs -I {} date -d @{} '+%Y-%m-%d %H:%M:%S' 2>/dev/null)

    if test -z "$current_rev"
        echo "Error: Could not read current nixpkgs revision from flake.lock"
        return 1
    end

    echo "Current nixpkgs:"
    echo "  Revision: $current_rev"
    echo "  Date: $current_date"
    echo ""

    # Check what the latest would be
    echo "Checking latest nixpkgs-unstable..."
    set -l temp_dir (mktemp -d)

    # Create a temporary flake just to check the latest revision
    echo '{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  outputs = { nixpkgs, ... }: {};
}' > $temp_dir/flake.nix

    nix flake lock $temp_dir --quiet 2>/dev/null

    set -l latest_rev (jq -r '.nodes.nixpkgs.locked.rev' $temp_dir/flake.lock 2>/dev/null)
    set -l latest_date (jq -r '.nodes.nixpkgs.locked.lastModified' $temp_dir/flake.lock 2>/dev/null | xargs -I {} date -d @{} '+%Y-%m-%d %H:%M:%S' 2>/dev/null)

    rm -rf $temp_dir

    if test -z "$latest_rev"
        echo "Error: Could not fetch latest nixpkgs revision"
        return 1
    end

    echo "Latest nixpkgs-unstable:"
    echo "  Revision: $latest_rev"
    echo "  Date: $latest_date"
    echo ""

    # Compare
    if test "$current_rev" = "$latest_rev"
        echo "════════════════════════════════════════════════"
        echo "✓ Already up to date!"
        echo "════════════════════════════════════════════════"
        echo ""
        echo "You're already on the latest nixpkgs-unstable."
        echo "Running 'nix-update -u' will not change any packages."
    else
        echo "════════════════════════════════════════════════"
        echo "📦 Updates available!"
        echo "════════════════════════════════════════════════"
        echo ""
        echo "Your nixpkgs is behind by:"

        # Try to show the commit log between versions
        set -l commits_behind (git -C ~/.nix-defexpr/channels_root/nixpkgs log --oneline $current_rev..$latest_rev 2>/dev/null | wc -l)
        if test $commits_behind -gt 0
            echo "  $commits_behind commits"
        else
            echo "  (Unable to calculate commit difference)"
        end

        echo ""
        echo "To see what changed:"
        echo "  https://github.com/NixOS/nixpkgs/compare/$current_rev...$latest_rev"
        echo ""
        echo "Run 'nix-update -u' to update and rebuild."
    end

    # Also check home-manager and other inputs
    echo ""
    echo "Other inputs:"

    set -l hm_current (jq -r '.nodes["home-manager"].locked.rev' $flake_dir/flake.lock 2>/dev/null)
    set -l hm_date (jq -r '.nodes["home-manager"].locked.lastModified' $flake_dir/flake.lock 2>/dev/null | xargs -I {} date -d @{} '+%Y-%m-%d' 2>/dev/null)

    if test -n "$hm_current"
        echo "  home-manager: $hm_current ($hm_date)"
    end
end
