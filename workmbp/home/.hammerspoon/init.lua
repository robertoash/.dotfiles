-- ============================================================================
-- Hammerspoon Configuration
-- ============================================================================
-- Main entry point that orchestrates the entire Hammerspoon setup
-- Organization inspired by nvim config structure for maintainability
--
-- Load order:
--   1. Load options and machine detection
--   2. Load utilities and helpers
--   3. Load modules (window management, hotkeys, etc.)
--   4. Load keymaps (centralized hotkey configuration)
--   5. Start watchers and services
-- ============================================================================

-- ============================================================================
-- 1. Load Base Configuration
-- ============================================================================
require("config.options")      -- HS settings and machine detection
require("config.constants")    -- Shared constants

-- Enable AppleScript support for debugging
hs.allowAppleScript(true)

-- ============================================================================
-- 2. Load Utilities & Spoons
-- ============================================================================
require("utils.helpers")        -- Shared helper functions
require("utils.logger")         -- Logging utilities
require("utils.notifications")  -- Custom toast notification system with stacking

-- Load and initialize LeftRightHotkey Spoon for distinguishing left/right modifiers
LeftRightHotkey = hs.loadSpoon("LeftRightHotkey")
if LeftRightHotkey then
    LeftRightHotkey:start()
    hs.logger.new('init', 'info'):i("LeftRightHotkey Spoon loaded")
else
    hs.logger.new('init', 'warning'):w("LeftRightHotkey Spoon not found - left/right modifier distinction unavailable")
end

-- ============================================================================
-- 3. Load Modules
-- ============================================================================
require("modules.app-launcher")       -- Application launching (skhd replacement)
require("modules.window-focus")       -- AutoRaise replacement
require("modules.text-expansion")     -- Text expansion (espanso replacement)
require("modules.window-management")  -- Amethyst replacement - intelligent tiling
require("modules.spaces")             -- Workspace/space management (replaces native macOS binds)
require("modules.pc-shortcuts")       -- PC-style shortcuts (Ctrl+C/V, etc.)
-- require("modules.window-shortcuts")   -- Window manipulation shortcuts (future)
-- require("modules.display")            -- Display management (future)
-- require("modules.menubar")            -- Optional: menubar widgets (future)

-- ============================================================================
-- 4. Load Keymaps (Centralized)
-- ============================================================================
require("config.keymaps")      -- ALL hotkeys defined here

-- ============================================================================
-- 5. Health Monitoring & Diagnostics
-- ============================================================================

-- Diagnostic system to detect stuck states and blocked event processing
local Diagnostics = {
    last_event_time = 0,
    health_check_timer = nil,
    check_interval = 30, -- seconds
}

local diag_log = hs.logger.new('diagnostics', 'info')

-- Health check to detect stuck states
function Diagnostics.check_system_health()
    local now = hs.timer.secondsSinceEpoch()
    diag_log.d(string.format("🔍 Health check: last_event=%.1fs ago", now - Diagnostics.last_event_time))
    
    -- Check for stuck flags
    local stuck_flags = {}
    
    if WindowFocusEvents and WindowFocusEvents.ignore_focus_events then
        table.insert(stuck_flags, "ignore_focus_events")
    end
    
    if WindowManagement and WindowManagement.space_change_in_progress then
        table.insert(stuck_flags, "space_change_in_progress")
    end

    -- Check for stuck windows in windows_being_moved
    if WindowManagement and WindowManagement.windows_being_moved then
        local stuck_count = 0
        for _ in pairs(WindowManagement.windows_being_moved) do
            stuck_count = stuck_count + 1
        end
        if stuck_count > 0 then
            table.insert(stuck_flags, string.format("windows_being_moved(%d)", stuck_count))
        end
    end

    if #stuck_flags > 0 then
        diag_log.w(string.format("⚠️ STUCK FLAGS DETECTED: %s", table.concat(stuck_flags, ", ")))
        -- Auto-reset stuck flags
        if WindowFocusEvents then
            WindowFocusEvents.ignore_focus_events = false
        end
        if WindowManagement then
            WindowManagement.space_change_in_progress = false
            WindowManagement.windows_being_moved = {}
        end
        Helpers.toast("🔄 Reset stuck flags", 1.0)
    end
    
    -- Check timer count (too many can cause blocking)
    local active_timers = 0
    pcall(function()
        active_timers = #hs.timer.running()
    end)
    
    if active_timers > 20 then
        diag_log.w(string.format("⚠️ HIGH TIMER COUNT: %d active timers", active_timers))
        Helpers.toast(string.format("⚠️ %d active timers", active_timers), 1.0)
    end
end

-- Track event activity (called by various event handlers)
function Diagnostics.mark_event_activity()
    Diagnostics.last_event_time = hs.timer.secondsSinceEpoch()
end

-- Start health monitoring
function Diagnostics.start()
    if Diagnostics.health_check_timer then
        Diagnostics.health_check_timer:stop()
    end
    
    Diagnostics.health_check_timer = hs.timer.doEvery(Diagnostics.check_interval, Diagnostics.check_system_health)
    diag_log.i("🏥 Health monitoring started (30s intervals)")
end

-- Add global diagnostic functions
function hs_reset_stuck_flags()
    diag_log.i("🔄 MANUAL RESET: Clearing all stuck flags")
    if WindowFocusEvents then
        WindowFocusEvents.ignore_focus_events = false
    end
    if WindowManagement then
        WindowManagement.ignore_resize_events = false
        WindowManagement.space_change_in_progress = false
    end
    if Spaces and Spaces.close_timer then
        Spaces.close_timer:stop()
        Spaces.close_timer = nil
    end
    Helpers.toast("✅ Reset all stuck flags", 1.5)
end

function hs_status()
    local status = {}
    
    if WindowFocusEvents then
        table.insert(status, string.format("ignore_focus: %s", WindowFocusEvents.ignore_focus_events and "ON" or "off"))
    end
    
    if WindowManagement then
        table.insert(status, string.format("space_change: %s", WindowManagement.space_change_in_progress and "ON" or "off"))

        -- Show time since last tiling
        local time_since_tiling = hs.timer.secondsSinceEpoch() - WindowManagement.last_tiling_time
        table.insert(status, string.format("last_tiling: %.2fs ago", time_since_tiling))

        -- Count windows being moved
        local move_count = 0
        if WindowManagement.windows_being_moved then
            for _ in pairs(WindowManagement.windows_being_moved) do
                move_count = move_count + 1
            end
        end
        table.insert(status, string.format("moving_windows: %d", move_count))
    end
    
    local timer_count = 0
    pcall(function() timer_count = #hs.timer.running() end)
    table.insert(status, string.format("timers: %d", timer_count))
    
    local now = hs.timer.secondsSinceEpoch()
    local last_event_ago = now - Diagnostics.last_event_time
    table.insert(status, string.format("last_event: %.1fs ago", last_event_ago))
    
    Helpers.toast(table.concat(status, " | "), 3.0)
    diag_log.i("📊 STATUS: " .. table.concat(status, " | "))
end

-- Start diagnostics
Diagnostics.start()

-- Show toast notification when config is loaded
Helpers.toast("Hammerspoon ready", 0.8)
