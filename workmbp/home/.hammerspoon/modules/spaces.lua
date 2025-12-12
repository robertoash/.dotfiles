-- ============================================================================
-- Spaces Module
-- ============================================================================
-- macOS Spaces/Mission Control management
-- Replaces: Native macOS space switching keybinds (Option+h/l)
--
-- Features:
-- - Next/previous space switching (Option+l/h)
-- - Move window to space
-- - Visual feedback showing space number
-- ============================================================================

Spaces = Spaces or {}

local log = hs.logger.new('spaces', 'info')

-- State
Spaces.mission_control_open = false
Spaces.close_timer = nil

-- ============================================================================
-- Mission Control Management
-- ============================================================================

-- Close Mission Control after a brief delay
local function close_mission_control_delayed()
    if Spaces.close_timer then
        Spaces.close_timer:stop()
        Spaces.close_timer = nil
    end

    Spaces.close_timer = hs.timer.doAfter(0.2, function()
        if Spaces.mission_control_open then
            hs.spaces.closeMissionControl()
            Spaces.mission_control_open = false
            log.d("Closed Mission Control")
        end
        Spaces.close_timer = nil
    end)
end

-- Eventtap to detect Option key release
Spaces.modifier_watcher = hs.eventtap.new({hs.eventtap.event.types.flagsChanged}, function(event)
    local flags = event:getFlags()

    -- If Option key was released and Mission Control is open, close it
    if not flags.alt and Spaces.mission_control_open then
        close_mission_control_delayed()
    end

    return false  -- Don't block the event
end):start()

-- ============================================================================
-- Space Navigation
-- ============================================================================

-- Get all spaces for current screen
local function get_current_screen_spaces()
    local screen = hs.screen.mainScreen()
    local spaces = hs.spaces.spacesForScreen(screen)
    return spaces or {}
end

-- Get current space ID
local function get_current_space()
    local screen = hs.screen.mainScreen()
    return hs.spaces.focusedSpace()
end

-- Switch to next space
function Spaces.switch_to_next()
    -- Mark diagnostic activity
    if Diagnostics and Diagnostics.mark_event_activity then
        Diagnostics.mark_event_activity()
    end
    
    local spaces = get_current_screen_spaces()
    if #spaces <= 1 then
        log.d("Only one space on current screen")
        Notifications.error("Only 1 space on this monitor", 1.0)
        return
    end

    local current = get_current_space()

    -- Find current space index
    local current_index = nil
    for i, space_id in ipairs(spaces) do
        if space_id == current then
            current_index = i
            break
        end
    end

    if not current_index then
        log.w("Could not find current space")
        Notifications.error("Could not find current space", 1.0)
        return
    end

    -- Calculate next index (wrap around)
    local next_index = (current_index % #spaces) + 1

    -- Hide all borders instantly before animation starts to prevent them showing during transition
    if WindowBorders then
        WindowBorders.hide_all()
    end

    -- Use non-standard Cmd+Shift+´ for space switching (won't conflict with any app)
    hs.eventtap.keyStroke({"cmd", "shift"}, "´", 0)

    -- Show toast after space switch completes
    hs.timer.doAfter(0.5, function()
        log.f("Switched to space %d/%d", next_index, #spaces)
        Notifications.toast(string.format("Space %d/%d", next_index, #spaces), 0.5)
    end)
end

-- Switch to previous space
function Spaces.switch_to_previous()
    -- Mark diagnostic activity
    if Diagnostics and Diagnostics.mark_event_activity then
        Diagnostics.mark_event_activity()
    end
    
    local spaces = get_current_screen_spaces()
    if #spaces <= 1 then
        log.d("Only one space on current screen")
        Notifications.error("Only 1 space on this monitor", 1.0)
        return
    end

    local current = get_current_space()

    -- Find current space index
    local current_index = nil
    for i, space_id in ipairs(spaces) do
        if space_id == current then
            current_index = i
            break
        end
    end

    if not current_index then
        log.w("Could not find current space")
        Notifications.error("Could not find current space", 1.0)
        return
    end

    -- Calculate previous index (wrap around)
    local prev_index = current_index == 1 and #spaces or current_index - 1

    -- Hide all borders instantly before animation starts to prevent them showing during transition
    if WindowBorders then
        WindowBorders.hide_all()
    end

    -- Use non-standard Cmd+´ for space switching (won't conflict with any app)
    hs.eventtap.keyStroke({"cmd"}, "´", 0)

    -- Show toast after space switch completes
    hs.timer.doAfter(0.5, function()
        log.f("Switched to space %d/%d", prev_index, #spaces)
        Notifications.toast(string.format("Space %d/%d", prev_index, #spaces), 0.5)
    end)
end

-- ============================================================================
-- Window Movement
-- ============================================================================

-- Move focused window to space and follow
function Spaces.move_window_to_space(space_num)
    local win = hs.window.focusedWindow()
    if not win then
        log.w("No focused window")
        return
    end

    local spaces = get_current_screen_spaces()
    if space_num < 1 or space_num > #spaces then
        log.w(string.format("Space %d does not exist (have %d spaces)", space_num, #spaces))
        Notifications.error(string.format("Only %d spaces available", #spaces), 1.0)
        return
    end

    local target_space = spaces[space_num]
    local win_id = win:id()
    local origin_screen = win:screen()

    -- Remove window from origin space's window_order
    if origin_screen and WindowManagement then
        local screen_id = origin_screen:id()
        local space_id = tostring(hs.spaces.focusedSpace())

        if WindowManagement.window_order[screen_id] and WindowManagement.window_order[screen_id][space_id] then
            local order = WindowManagement.window_order[screen_id][space_id]
            for i, id in ipairs(order) do
                if id == win_id then
                    table.remove(order, i)
                    log.i(string.format("🗑️  Removed window %d from origin space order", win_id))
                    break
                end
            end
        end
    end

    -- Move window to space
    hs.spaces.moveWindowToSpace(win, target_space)

    -- Retile origin space (window already removed from order)
    if origin_screen and WindowManagement then
        WindowManagement.tile_screen(origin_screen)
    end

    -- Follow the window to the new space
    hs.spaces.gotoSpace(target_space)

    -- Show toast after space switch completes
    hs.timer.doAfter(0.5, function()
        log.f("Moved window to space %d/%d", space_num, #spaces)
        Notifications.toast(string.format("→ Space %d/%d", space_num, #spaces), 0.5)
    end)
end

-- Move focused window to next space
function Spaces.move_window_to_next()
    log.i("🚀 MOVE_WINDOW_TO_NEXT CALLED")

    local spaces = get_current_screen_spaces()
    if #spaces <= 1 then
        log.d("Only one space on current screen")
        Notifications.error("Only 1 space on this monitor", 1.0)
        return
    end

    local win = hs.window.focusedWindow()
    if not win then
        log.w("No focused window")
        Notifications.error("No window focused", 1.0)
        return
    end

    local current = get_current_space()

    -- Find current space index
    local current_index = nil
    for i, space_id in ipairs(spaces) do
        if space_id == current then
            current_index = i
            break
        end
    end

    if not current_index then
        log.w("Could not find current space")
        return
    end

    -- Calculate next index (wrap around)
    local next_index = (current_index % #spaces) + 1

    local win_id = win:id()
    local origin_screen = win:screen()

    -- Remove window from origin space's window_order
    if origin_screen and WindowManagement then
        local screen_id = origin_screen:id()
        local space_id = tostring(hs.spaces.focusedSpace())

        if WindowManagement.window_order[screen_id] and WindowManagement.window_order[screen_id][space_id] then
            local order = WindowManagement.window_order[screen_id][space_id]
            for i, id in ipairs(order) do
                if id == win_id then
                    table.remove(order, i)
                    log.i(string.format("🗑️  Removed window %d from origin space order", win_id))
                    break
                end
            end
        end
    end

    -- WORKAROUND: Use native macOS shortcut (Ctrl+Alt+L = Move right a space)
    -- This triggers symbolic hotkey 82 which moves window to next space
    hs.eventtap.keyStroke({"ctrl", "alt"}, "l", 0)

    -- Wait briefly for the move to complete
    hs.timer.doAfter(0.1, function()
        -- Retile origin space (window already removed from order)
        if origin_screen and WindowManagement then
            WindowManagement.tile_screen(origin_screen)
        end

        local next_space = spaces[next_index]
        hs.spaces.gotoSpace(next_space)

        -- Show toast after space switch completes
        hs.timer.doAfter(0.5, function()
            log.f("Moved window to space %d/%d", next_index, #spaces)
            Notifications.toast(string.format("→ Space %d/%d", next_index, #spaces), 0.5)
        end)
    end)
end

-- Move focused window to previous space
function Spaces.move_window_to_previous()
    local spaces = get_current_screen_spaces()
    if #spaces <= 1 then
        log.d("Only one space on current screen")
        Notifications.error("Only 1 space on this monitor", 1.0)
        return
    end

    local win = hs.window.focusedWindow()
    if not win then
        log.w("No focused window")
        Notifications.error("No window focused", 1.0)
        return
    end

    local current = get_current_space()

    -- Find current space index
    local current_index = nil
    for i, space_id in ipairs(spaces) do
        if space_id == current then
            current_index = i
            break
        end
    end

    if not current_index then
        log.w("Could not find current space")
        return
    end

    -- Calculate previous index (wrap around)
    local prev_index = current_index == 1 and #spaces or current_index - 1

    local win_id = win:id()
    local origin_screen = win:screen()

    -- Remove window from origin space's window_order
    if origin_screen and WindowManagement then
        local screen_id = origin_screen:id()
        local space_id = tostring(hs.spaces.focusedSpace())

        if WindowManagement.window_order[screen_id] and WindowManagement.window_order[screen_id][space_id] then
            local order = WindowManagement.window_order[screen_id][space_id]
            for i, id in ipairs(order) do
                if id == win_id then
                    table.remove(order, i)
                    log.i(string.format("🗑️  Removed window %d from origin space order", win_id))
                    break
                end
            end
        end
    end

    -- WORKAROUND: Use native macOS shortcut (Ctrl+Alt+H = Move left a space)
    -- This triggers symbolic hotkey 80 which moves window to previous space
    hs.eventtap.keyStroke({"ctrl", "alt"}, "h", 0)

    -- Wait briefly for the move to complete
    hs.timer.doAfter(0.1, function()
        -- Retile origin space (window already removed from order)
        if origin_screen and WindowManagement then
            WindowManagement.tile_screen(origin_screen)
        end

        local prev_space = spaces[prev_index]
        hs.spaces.gotoSpace(prev_space)

        -- Show toast after space switch completes
        hs.timer.doAfter(0.5, function()
            log.f("Moved window to space %d/%d", prev_index, #spaces)
            Notifications.toast(string.format("→ Space %d/%d", prev_index, #spaces), 0.5)
        end)
    end)
end

-- ============================================================================
-- Info
-- ============================================================================

-- Show current space info
function Spaces.show_current_space()
    local spaces = get_current_screen_spaces()
    local current = get_current_space()

    local current_index = nil
    for i, space_id in ipairs(spaces) do
        if space_id == current then
            current_index = i
            break
        end
    end

    if current_index then
        Notifications.toast(string.format("Space %d/%d", current_index, #spaces), 2.0)
    end
end

log.i("Spaces module loaded")

return Spaces
