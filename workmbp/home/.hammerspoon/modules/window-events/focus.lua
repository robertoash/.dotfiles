-- ============================================================================
-- Window Focus Event Handler
-- ============================================================================
-- Tracks which window is focused on each screen
-- NEVER triggers retiling - that's handled by structural events only
-- ============================================================================

WindowFocusEvents = WindowFocusEvents or {}

local log = hs.logger.new('window-focus-events', 'info')

-- Last focused window per screen per space
-- Structure: last_focused[screen_id][space_id] = window_id
WindowFocusEvents.last_focused = {}

-- State
WindowFocusEvents.watcher = nil

-- Flag to temporarily disable focus tracking during programmatic focus changes
WindowFocusEvents.ignore_focus_events = false

-- ============================================================================
-- Focus Tracking
-- ============================================================================

-- Get current space ID for a screen
local function get_space_id(screen)
    local success, result = pcall(function()
        return hs.spaces.activeSpaceOnScreen(screen)
    end)

    if success and result then
        return tostring(result)
    end

    return "default"
end

-- Track window focus per screen per space (NEVER triggers retiling)
local function on_window_focused(window)
    if not window then return end
    
    -- Mark diagnostic activity
    if Diagnostics and Diagnostics.mark_event_activity then
        Diagnostics.mark_event_activity()
    end

    -- Skip tracking if we're in the middle of programmatic focus changes
    if WindowFocusEvents.ignore_focus_events then
        log.d(string.format("Ignoring focus event for: %s (programmatic focus in progress)", window:title()))
        return
    end

    -- Only track tileable windows
    if not WindowManagement.is_tileable(window) then
        return
    end

    local screen = window:screen()
    if screen then
        local screen_id = WindowManagement.get_screen_id(screen)
        local space_id = get_space_id(screen)

        -- Initialize nested table structure if needed
        if not WindowFocusEvents.last_focused[screen_id] then
            WindowFocusEvents.last_focused[screen_id] = {}
        end

        local old_window_id = WindowFocusEvents.last_focused[screen_id][space_id]
        local win_id = window:id()
        WindowFocusEvents.last_focused[screen_id][space_id] = win_id
        log.i(string.format("👁️  FOCUS EVENT: %s (ID: %s) on screen %s, space %s [was: %s]",
            window:title(), win_id, screen:name(), space_id, old_window_id or "nil"))

        -- On ANY focus event, check if HS-launched windows moved between screens
        -- Update position cache and retile involved screens if changed
        for hs_win_id, _ in pairs(WindowManagement.hs_launched_windows) do
            local hs_win = hs.window.find(hs_win_id)
            if hs_win and WindowManagement.is_tileable(hs_win) then
                local current_screen = hs_win:screen()
                if current_screen then
                    local cached_screen_id = WindowManagement.hs_launched_window_screens[hs_win_id]
                    local current_screen_id = WindowManagement.get_screen_id(current_screen)

                    if cached_screen_id and cached_screen_id ~= current_screen_id then
                        -- Window moved between screens - retile both origin and destination
                        local cached_screen = hs.screen.find(cached_screen_id)
                        if cached_screen then
                            log.i(string.format("🖥️  HS-launched window %d moved from %s to %s",
                                hs_win_id, cached_screen:name(), current_screen:name()))

                            -- Retile both screens
                            hs.timer.doAfter(0.1, function()
                                WindowManagement.tile_screen(cached_screen)
                                WindowManagement.tile_screen(current_screen)
                                log.i(string.format("   ✓ Retiled origin (%s) and destination (%s)",
                                    cached_screen:name(), current_screen:name()))
                            end)
                        end
                    end

                    -- Update position cache
                    WindowManagement.hs_launched_window_screens[hs_win_id] = current_screen_id
                end
            end
        end

        -- Clear focus-follows-mouse last_window tracker to allow immediate refocus
        -- This fixes the issue where keyboard focus changes prevent mouse focus
        -- from working until you leave and re-enter the window
        if WindowFocus then
            WindowFocus.last_window = nil
        end

        -- Update border colors on focus change
        if WindowBorders then
            WindowBorders.update_focus()
        end

        -- Enforce top gap on untiled screens (catches windows that don't fire movement events)
        if WindowManagement then
            WindowManagement.enforce_top_gap(window)
        end
    end
end

-- ============================================================================
-- Module Control
-- ============================================================================

function WindowFocusEvents.start()
    if WindowFocusEvents.watcher then
        log.w("Focus tracking already started")
        return
    end

    log.i("Starting focus tracking")

    -- Use application watcher to catch ALL focus events (not window filter)
    -- Window filters have issues where windows created after filter initialization
    -- don't trigger events, especially for windows launched via Hammerspoon keybinds
    WindowFocusEvents.watcher = hs.application.watcher.new(function(appName, eventType, app)
        if eventType == hs.application.watcher.activated then
            -- An application was activated, check its focused window
            if app then
                local win = app:focusedWindow()
                if win then
                    on_window_focused(win)
                end
            end
        end
    end)

    WindowFocusEvents.watcher:start()
    log.i("Focus tracking started (using application watcher)")
end

function WindowFocusEvents.stop()
    log.i("Stopping focus tracking")

    if WindowFocusEvents.watcher then
        WindowFocusEvents.watcher:stop()
        WindowFocusEvents.watcher = nil
    end

    log.i("Focus tracking stopped")
end

-- Get last focused window ID for a screen and space
function WindowFocusEvents.get_last_focused(screen_id, space_id)
    if not WindowFocusEvents.last_focused[screen_id] then
        return nil
    end
    return WindowFocusEvents.last_focused[screen_id][space_id]
end

log.i("Window focus events module loaded")

return WindowFocusEvents
