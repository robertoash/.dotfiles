-- ============================================================================
-- Window Focus Module
-- ============================================================================
-- Focus follows mouse (without raising)
-- Replaces: autoraise (but simpler - just focus, no raise)
-- ============================================================================

WindowFocus = WindowFocus or {}

local log = hs.logger.new('window-focus', 'info')

-- State
WindowFocus.watcher = nil
WindowFocus.timer = nil
WindowFocus.last_window = nil
WindowFocus.last_mouse_pos = nil
WindowFocus.enabled = false
WindowFocus.dragging = false  -- Disable focus-follows-mouse during window drag

-- ============================================================================
-- Focus Follows Mouse Implementation
-- ============================================================================

-- Get window under mouse, tile-aware
-- For tiled windows, considers the entire tile area (not just actual window frame)
local function get_window_under_mouse_tile_aware()
    local mouse_pos = hs.mouse.absolutePosition()

    -- If window management is available, check tiled windows first
    -- This ensures proportional-tile windows (like System Settings) maintain focus
    -- even when the mouse is in empty space within their tile
    if WindowManagement then
        local screens = hs.screen.allScreens()
        for _, screen in ipairs(screens) do
            local screen_frame = screen:frame()
            -- Check if mouse is on this screen
            if mouse_pos.x >= screen_frame.x and mouse_pos.x <= screen_frame.x + screen_frame.w and
               mouse_pos.y >= screen_frame.y and mouse_pos.y <= screen_frame.y + screen_frame.h then
                -- Get expected frames for tiled windows on this screen
                local all_windows = hs.window.allWindows()
                for _, win in ipairs(all_windows) do
                    if win:isVisible() and win:screen() == screen and WindowManagement.is_tileable(win) then
                        -- Check expected (tile) frame first
                        local expected_frame = WindowManagement.expected_frames[win:id()]
                        if expected_frame then
                            if mouse_pos.x >= expected_frame.x and mouse_pos.x <= expected_frame.x + expected_frame.w and
                               mouse_pos.y >= expected_frame.y and mouse_pos.y <= expected_frame.y + expected_frame.h then
                                return win
                            end
                        end
                    end
                end
            end
        end
    end

    -- Fall back to standard window-under-mouse detection
    return Helpers.get_window_under_mouse()
end

-- Focus window under mouse
local function focus_window_under_mouse()
    local win = get_window_under_mouse_tile_aware()

    if not win then
        return
    end

    -- Skip focus-follows-mouse on built-in display
    local screen = win:screen()
    if screen and WindowManagement and WindowManagement.is_builtin_screen then
        if WindowManagement.is_builtin_screen(screen) then
            return
        end
    end

    -- Don't refocus the same window
    if WindowFocus.last_window and win:id() == WindowFocus.last_window:id() then
        return
    end

    -- Focus and raise the window (macOS requires raising for keyboard input)
    win:focus()
    WindowFocus.last_window = win
    log.i(string.format("🎯 Focus-follows-mouse: %s", win:title() or "unknown"))

    -- Border update happens automatically via WindowFocusEvents.on_window_focused
    -- No need for delayed update here
end

-- ============================================================================
-- Module Control
-- ============================================================================

-- Timer callback to check mouse position
local function check_mouse_position()
    if not Config.preferences.focus_follows_mouse then
        return
    end

    -- Disable focus-follows-mouse during window drag
    if WindowFocus.dragging then
        return
    end

    local mouse_pos = hs.mouse.absolutePosition()

    -- Only check if mouse actually moved (reduces unnecessary work)
    if WindowFocus.last_mouse_pos and
       mouse_pos.x == WindowFocus.last_mouse_pos.x and
       mouse_pos.y == WindowFocus.last_mouse_pos.y then
        return
    end

    WindowFocus.last_mouse_pos = mouse_pos
    focus_window_under_mouse()
end

-- Start focus follows mouse
function WindowFocus.start()
    if WindowFocus.enabled then
        log.w("Focus follows mouse already enabled")
        return
    end

    log.i("Starting focus follows mouse")

    -- Use timer-based polling (more reliable than eventtap for mouse moves)
    local interval = Config.preferences.focus_follows_mouse_interval or 0.1
    WindowFocus.timer = hs.timer.new(interval, check_mouse_position)
    WindowFocus.timer:start()

    WindowFocus.enabled = true

    log.i(string.format("Focus follows mouse started (timer-based, %dms interval)", interval * 1000))
end

-- Stop focus follows mouse
function WindowFocus.stop()
    if not WindowFocus.enabled then
        log.w("Focus follows mouse already disabled")
        return
    end

    log.i("Stopping focus follows mouse")

    if WindowFocus.timer then
        WindowFocus.timer:stop()
        WindowFocus.timer = nil
    end

    WindowFocus.last_window = nil
    WindowFocus.last_mouse_pos = nil
    WindowFocus.enabled = false

    log.i("Focus follows mouse stopped")
end

-- Toggle focus follows mouse
function WindowFocus.toggle()
    if WindowFocus.enabled then
        WindowFocus.stop()
        Helpers.alert("Focus follows mouse disabled")
    else
        WindowFocus.start()
        Helpers.alert("Focus follows mouse enabled")
    end
end

-- ============================================================================
-- Auto-start
-- ============================================================================

if Config.preferences.focus_follows_mouse then
    WindowFocus.start()
end

log.i("Window focus module loaded")

return WindowFocus
