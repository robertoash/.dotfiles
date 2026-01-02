# Remove your current npm block entirely and replace with:

# Lazy npm setup - only runs when you actually use npm
function npm
    # Check if we've already set up npm in this session
    if not set -q __npm_setup_done
        echo "🔧 Setting up npm environment..." >&2
        # Unset the problematic override to let ~/.npmrc prefix take effect
        set -e NPM_CONFIG_PREFIX
        set -gx NPM_PREFIX (command npm config get prefix)
        fish_add_path "$NPM_PREFIX/bin"
        set -g __npm_setup_done 1
    end
    # Run the actual npm command
    command npm $argv
end