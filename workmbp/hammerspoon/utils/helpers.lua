-- ============================================================================
-- Helper Functions
-- ============================================================================
-- Shared utility functions used across modules
-- ============================================================================

Helpers = Helpers or {}

-- ============================================================================
-- String Helpers
-- ============================================================================

-- Check if a string starts with a prefix
function Helpers.starts_with(str, prefix)
    return str:sub(1, #prefix) == prefix
end

-- Check if a string ends with a suffix
function Helpers.ends_with(str, suffix)
    return str:sub(-#suffix) == suffix
end

-- Trim whitespace from string
function Helpers.trim(str)
    return str:match("^%s*(.-)%s*$")
end

-- ============================================================================
-- Table Helpers
-- ============================================================================

-- Check if table contains value
function Helpers.table_contains(table, value)
    for _, v in pairs(table) do
        if v == value then
            return true
        end
    end
    return false
end

-- Get table size
function Helpers.table_size(table)
    local count = 0
    for _ in pairs(table) do
        count = count + 1
    end
    return count
end

-- ============================================================================
-- Application Helpers
-- ============================================================================

-- Launch application by path
function Helpers.launch_app(app_path, args)
    args = args or {}
    local success = hs.application.open(app_path)
    if not success then
        hs.alert.show("Failed to launch: " .. app_path)
        return false
    end
    return true
end

-- Get frontmost application
function Helpers.get_frontmost_app()
    return hs.application.frontmostApplication()
end

-- Focus application by name
function Helpers.focus_app(app_name)
    local app = hs.application.get(app_name)
    if app then
        app:activate()
        return true
    end
    return false
end

-- ============================================================================
-- Window Helpers
-- ============================================================================

-- Get focused window
function Helpers.get_focused_window()
    return hs.window.focusedWindow()
end

-- Get all visible windows
function Helpers.get_visible_windows()
    return hs.window.visibleWindows()
end

-- Get window under mouse (returns topmost window at mouse position)
function Helpers.get_window_under_mouse()
    local mouse_pos = hs.mouse.absolutePosition()
    -- allWindows() returns all windows (includes non-standard windows like Hammerspoon Console)
    -- We'll need to manually sort by Z-order if needed
    local windows = hs.window.allWindows()

    for _, win in ipairs(windows) do
        if win:isVisible() then
            local frame = win:frame()
            if mouse_pos.x >= frame.x and mouse_pos.x <= frame.x + frame.w and
               mouse_pos.y >= frame.y and mouse_pos.y <= frame.y + frame.h then
                -- Return the first (topmost) window that matches
                return win
            end
        end
    end

    return nil
end

-- ============================================================================
-- Keystroke Helpers
-- ============================================================================

-- Send keystroke to system
function Helpers.send_keystroke(mods, key)
    hs.eventtap.keyStroke(mods, key, 0)
end

-- Type string (for text expansion)
function Helpers.type_string(str)
    hs.eventtap.keyStrokes(str)
end

-- Delete characters (for removing expansion trigger)
function Helpers.delete_chars(count)
    for _ = 1, count do
        hs.eventtap.keyStroke({}, "delete", 0)
    end
end

-- ============================================================================
-- Notification Helpers
-- ============================================================================

-- Show notification
function Helpers.notify(title, message, sound)
    sound = sound or false

    local notification = hs.notify.new({
        title = title,
        informativeText = message,
        withdrawAfter = 2,
    })

    if sound then
        notification:soundName(hs.notify.defaultNotificationSound)
    end

    notification:send()
end

-- Toast notification style (Android-like, subtle)
-- Bottom center, small font, more transparent
function Helpers.toast(message, duration)
    duration = duration or 1

    -- Configure toast style
    hs.alert.defaultStyle = {
        strokeColor = { white = 0, alpha = 0 },  -- No border
        strokeWidth = 0,  -- No border width
        fillColor = { white = 0.1, alpha = 0.85 },  -- Dark background, more transparent
        textColor = { white = 1, alpha = 1 },  -- White text
        textFont = "GeistMono Nerd Font",
        textSize = 14,  -- Smaller font
        radius = 8,  -- Rounded corners
        atScreenEdge = 2,  -- Bottom of screen (0=top, 1=left, 2=bottom, 3=right)
        fadeInDuration = 0.15,
        fadeOutDuration = 0.15,
        padding = 16,
    }

    hs.alert.show(message, duration)
end

-- Show alert (alias for toast for backward compatibility)
function Helpers.alert(message, duration)
    Helpers.toast(message, duration)
end

return Helpers
