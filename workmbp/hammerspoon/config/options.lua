-- ============================================================================
-- Hammerspoon Options and Machine Detection
-- ============================================================================
-- Global configuration options and environment detection
-- ============================================================================

-- Create global config table
Config = Config or {}

-- ============================================================================
-- Machine Detection
-- ============================================================================

-- Get hostname
Config.hostname = hs.host.localizedName()

-- Detect if this is work machine
function Config.is_work_mac()
    local hostname = Config.hostname
    return hostname:match("^rash%-workmbp") ~= nil or hostname:match("^workmbp") ~= nil
end

Config.is_work = Config.is_work_mac()

-- ============================================================================
-- Hammerspoon Settings
-- ============================================================================

-- Set log level (verbose for debugging, warning for production)
hs.logger.defaultLogLevel = "info"

-- Disable animation duration for faster window operations
hs.window.animationDuration = 0

-- Set up IPC for command line control
hs.ipc.cliInstall()

-- Console settings
hs.console.darkMode(true)
hs.console.consoleFont({name = "GeistMono Nerd Font", size = 14})

-- ============================================================================
-- User Preferences
-- ============================================================================

Config.preferences = {
    -- Window focus
    focus_follows_mouse = true,
    focus_follows_mouse_interval = 0.1,  -- Check every 100ms (balance between responsiveness and CPU usage)

    -- Text expansion
    text_expansion_enabled = true,

    -- Notifications
    show_notifications = true,
}

-- Debug helper
if Config.is_work then
    hs.printf("Running on work machine: %s", Config.hostname)
else
    hs.printf("Running on personal machine: %s", Config.hostname)
end
