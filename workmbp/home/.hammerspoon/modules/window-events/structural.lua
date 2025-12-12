-- ============================================================================
-- Window Structural Event Handler
-- ============================================================================
-- Handles window creation, destruction, visibility changes
-- These events trigger retiling to maintain layout
-- ============================================================================

WindowStructuralEvents = WindowStructuralEvents or {}

local log = hs.logger.new('window-structural-events', 'info')

-- State
WindowStructuralEvents.watcher = nil

-- ============================================================================
-- Event Handler
-- ============================================================================

-- Handle structural window events (create, destroy, show, hide)
local function on_window_event(win, app, event)
    -- Mark diagnostic activity
    if Diagnostics and Diagnostics.mark_event_activity then
        Diagnostics.mark_event_activity()
    end
    
    -- Log event for debugging
    local app_name = "unknown"
    if app then
        local success, name = pcall(function() return app:name() end)
        if success and name then
            app_name = name
        end
    end
    log.i(string.format("🔔 STRUCTURAL EVENT: %s (app: %s)", event, app_name))

    -- For window entering fullscreen, hide its border
    if event == hs.window.filter.windowFullscreened then
        local win_id = nil
        if win then
            pcall(function() win_id = win:id() end)
        end
        if win_id and WindowBorders then
            WindowBorders.remove_window(win_id)
            log.i("🔲 Hid border for fullscreen window")
        end
        return
    end

    -- For window exiting fullscreen, restore border and retile
    if event == hs.window.filter.windowUnfullscreened then
        hs.timer.doAfter(0.1, function()
            local success, screen = pcall(function()
                return win and win:screen()
            end)
            if success and screen then
                WindowManagement.tile_screen(screen)
                -- Enforce top gap on untiled screens
                WindowManagement.enforce_top_gap(win)
                if WindowBorders then
                    WindowBorders.update_all()
                end
                log.i("🔳 Restored border after exiting fullscreen")
            end
        end)
        return
    end

    -- For window leaving current space (drag-and-drop), retile origin
    if event == hs.window.filter.windowNotInCurrentSpace then
        local win_id = nil
        local screen = nil
        local win_title = "unknown"
        if win then
            pcall(function()
                win_id = win:id()
                screen = win:screen()
                win_title = win:title() or "untitled"
            end)
        end

        log.i(string.format("👋 Window %d (%s) leaving current space", win_id or 0, win_title))

        -- Hide border for window leaving current space
        if win_id and WindowBorders then
            WindowBorders.remove_window(win_id)
            log.i("   Hid border")
        end

        -- Retile origin space (get_tileable_windows will filter out the leaving window)
        if screen and WindowManagement then
            log.i(string.format("   Retiling origin screen %s", screen:name()))
            WindowManagement.tile_screen(screen)
            log.i("   ✓ Retile complete")
        end
        return
    end

    -- For window entering current space, restore border and retile
    if event == hs.window.filter.windowInCurrentSpace then
        hs.timer.doAfter(0.1, function()
            local success, screen = pcall(function()
                return win and win:screen()
            end)
            if success and screen then
                WindowManagement.tile_screen(screen)
                -- Enforce top gap on untiled screens
                WindowManagement.enforce_top_gap(win)
                if WindowBorders then
                    WindowBorders.update_all()
                end
                log.i("👋 Restored border for window entering space")
            end
        end)
        return
    end

    -- For window destruction/hidden/minimized events, retile with delay
    if event == hs.window.filter.windowDestroyed or
       event == hs.window.filter.windowHidden or
       event == hs.window.filter.windowMinimized then

        -- Get window ID and screen before destruction
        local win_id = nil
        local screen = nil
        if win then
            pcall(function()
                win_id = win:id()
                screen = win:screen()
            end)
        end

        -- Clean up tracking for destroyed windows
        if event == hs.window.filter.windowDestroyed and win_id then
            WindowManagement.window_previous_screen[win_id] = nil
        end

        -- Remove border immediately for destroyed/minimized/hidden windows
        if win_id and WindowBorders then
            WindowBorders.remove_window(win_id)
        end

        hs.timer.doAfter(0.05, function()
            -- Handle master destruction (reset mfact if needed)
            if event == hs.window.filter.windowDestroyed and win_id and screen then
                WindowManagement.handle_master_destroyed(win_id, screen)
            end

            -- Don't try to access the destroyed window, just retile all screens
            WindowManagement.tile_all_screens()
        end)
        return
    end

    -- For window moved events (drag and drop), handle reordering and retile
    if event == hs.window.filter.windowMoved then
        -- Skip windowMoved events during programmatic retiling
        if WindowManagement.ignore_resize_events then
            return
        end

        local win_id = nil
        local current_screen = nil
        if win then
            pcall(function()
                win_id = win:id()
                current_screen = win:screen()
            end)
        end

        -- Check if window moved between screens (cross-monitor move)
        local previous_screen = win_id and WindowManagement.window_previous_screen[win_id]
        local screen_changed = previous_screen and current_screen and
                              (previous_screen:id() ~= current_screen:id())

        if screen_changed then
            log.i(string.format("🖥️  Window %d moved from screen %s to %s (cross-monitor move)",
                win_id, previous_screen:name(), current_screen:name()))

            -- Retile origin screen after a delay to let the window finish moving visually
            hs.timer.doAfter(0.1, function()
                WindowManagement.tile_screen(previous_screen)
                log.i(string.format("   ✓ Retiled origin screen %s", previous_screen:name()))
            end)
        end

        -- Update previous screen tracking
        if win_id and current_screen then
            WindowManagement.window_previous_screen[win_id] = current_screen
        end

        hs.timer.doAfter(0.05, function()
            local success, screen = pcall(function()
                return win and win:screen()
            end)

            if success and screen then
                -- First, check if master window was manually resized
                local was_manual_resize = WindowManagement.detect_manual_resize(win, screen)

                if was_manual_resize then
                    -- Manual resize detected and mfact saved - retile to apply new mfact
                    WindowManagement.tile_screen(screen)
                else
                    -- Not a manual resize, must be drag-and-drop
                    -- Detect drop position and reorder windows accordingly
                    WindowManagement.handle_window_drop(win, screen)
                    -- Retile to reflect new order
                    WindowManagement.tile_screen(screen)
                end

                -- Enforce top gap on untiled screens with additional delay
                -- Some apps (like WezTerm) may reposition after the initial move
                hs.timer.doAfter(0.1, function()
                    WindowManagement.enforce_top_gap(win)
                end)
            end
        end)
        return
    end

    -- Use short delay to let window fully initialize
    local delay = (event == hs.window.filter.windowCreated) and 0.1 or 0.05
    local should_focus = (event == hs.window.filter.windowCreated or
                         event == hs.window.filter.windowVisible or
                         event == hs.window.filter.windowUnminimized)

    hs.timer.doAfter(delay, function()
        -- Check if window still exists and has a screen
        local success, screen = pcall(function()
            return win and win:screen()
        end)

        if success and screen then
            -- Initialize screen tracking for new/visible windows
            local win_id = nil
            pcall(function() win_id = win:id() end)
            if win_id then
                WindowManagement.window_previous_screen[win_id] = screen
            end

            WindowManagement.tile_screen(screen)

            -- Enforce top gap on untiled screens
            WindowManagement.enforce_top_gap(win)

            -- Focus newly created/visible/unminimized windows
            if should_focus and win then
                hs.timer.doAfter(0.05, function()
                    local still_exists = pcall(function() return win:id() end)
                    if still_exists and WindowManagement.is_tileable(win) then
                        -- For reliable focus on newly spawned windows:
                        -- 1. Activate the application (brings app to front)
                        -- 2. Raise the window (brings window to front within app)
                        -- 3. Focus the window (gives it keyboard input)
                        local app = win:application()
                        if app then
                            app:activate()
                        end
                        win:raise()
                        win:focus()
                        log.i(string.format("🎯 Auto-focused window: %s", win:title() or "unknown"))
                    end
                end)
            end
        else
            -- Window no longer exists or has no screen, retile all
            WindowManagement.tile_all_screens()
        end
    end)
end

-- ============================================================================
-- Module Control
-- ============================================================================

function WindowStructuralEvents.start()
    if WindowStructuralEvents.watcher then
        log.w("Structural event tracking already started")
        return
    end

    log.i("Starting structural event tracking")

    -- Watch for structural window events (NOT focus)
    local success, result = pcall(function()
        -- Use a permissive filter to catch all new windows
        local filter = hs.window.filter.new()
        filter:setDefaultFilter({}) -- Allow all windows

        return filter:subscribe({
            hs.window.filter.windowCreated,
            hs.window.filter.windowDestroyed,
            hs.window.filter.windowHidden,           -- Catch windows being hidden (Cmd+H)
            hs.window.filter.windowVisible,          -- Catch windows becoming visible
            hs.window.filter.windowMinimized,        -- Catch windows minimized to dock (Cmd+M)
            hs.window.filter.windowUnminimized,      -- Catch windows restored from dock
            hs.window.filter.windowFullscreened,     -- Catch windows entering fullscreen
            hs.window.filter.windowUnfullscreened,   -- Catch windows exiting fullscreen
            hs.window.filter.windowInCurrentSpace,   -- Catch windows entering current space (Mission Control)
            hs.window.filter.windowNotInCurrentSpace,-- Catch windows leaving current space
            hs.window.filter.windowMoved,            -- Catch windows being dragged to enable retiling
            -- Note: windowFocused is handled by focus.lua module
        }, on_window_event)
    end)

    if success then
        WindowStructuralEvents.watcher = result
        log.i("Structural event tracking started")
    else
        log.e("Failed to start structural event tracking (hs.spaces compatibility issue): " .. tostring(result))
        log.w("Structural event tracking disabled - windows will not auto-tile")
    end
end

function WindowStructuralEvents.stop()
    log.i("Stopping structural event tracking")

    if WindowStructuralEvents.watcher then
        WindowStructuralEvents.watcher:unsubscribeAll()
        WindowStructuralEvents.watcher = nil
    end

    log.i("Structural event tracking stopped")
end

log.i("Window structural events module loaded")

return WindowStructuralEvents
