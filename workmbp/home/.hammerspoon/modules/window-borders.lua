-- ============================================================================
-- Window Borders Module
-- ============================================================================
-- Draw borders around tileable windows (like Hyprland)
-- ============================================================================

WindowBorders = WindowBorders or {}

local log = hs.logger.new('window-borders', 'info')

-- Load centralized config
local Config = require("config")

-- State
WindowBorders.borders = {}  -- Map of window ID -> border canvas
WindowBorders.last_focused_id = nil  -- Track last focused window for efficient updates
WindowBorders.enabled = false

-- ============================================================================
-- Border Drawing
-- ============================================================================

-- Convert color config to canvas color format
local function get_fill_style(color_config)
    -- Return solid color directly
    return {
        red = color_config.red,
        green = color_config.green,
        blue = color_config.blue,
        alpha = color_config.alpha,
    }
end

-- Create border canvas for a window
local function create_border(win)
    if not win then return nil end

    local frame = win:frame()
    local radius = Config.borders.radius

    -- Determine if this is the focused window and if it's pinned
    local focused_win = hs.window.focusedWindow()
    local is_focused = focused_win and focused_win:id() == win:id()
    local is_pinned = WindowManagement and WindowManagement.pinned_windows[win:id()] ~= nil

    -- Select appropriate color and width based on focus and pin status
    local color_config
    local width
    if is_pinned then
        color_config = is_focused and Config.borders.pinned_focused or Config.borders.pinned_unfocused
        width = is_focused and Config.borders.width_focused or Config.borders.width_unfocused
    else
        color_config = is_focused and Config.borders.focused or Config.borders.unfocused
        width = is_focused and Config.borders.width_focused or Config.borders.width_unfocused
    end

    local fill_style = get_fill_style(color_config)

    -- Create canvas that covers window + border (using max width for canvas size)
    local max_width = Config.borders.width_focused
    local canvas = hs.canvas.new({
        x = frame.x - max_width,
        y = frame.y - max_width,
        w = frame.w + (max_width * 2),
        h = frame.h + (max_width * 2),
    })

    -- Set canvas behavior
    -- Use stationary to prevent borders from animating with Mission Control
    -- canJoinAllSpaces allows borders to follow windows across spaces
    canvas:behavior(hs.canvas.windowBehaviors.stationary +
                    hs.canvas.windowBehaviors.canJoinAllSpaces)
    -- Use floating level to appear above windows and their shadows
    canvas:level(hs.canvas.windowLevels.floating)
    canvas:clickActivating(false)

    -- Draw border as stroked rounded rectangle
    canvas[1] = {
        type = "rectangle",
        action = "stroke",
        strokeColor = fill_style,
        strokeWidth = width,
        roundedRectRadii = { xRadius = radius, yRadius = radius },
        frame = {
            x = max_width / 2,
            y = max_width / 2,
            w = frame.w + max_width,
            h = frame.h + max_width,
        },
    }

    canvas:show()
    return canvas
end

-- Update border position and size
local function update_border(win)
    if not win then return end

    local win_id = win:id()
    local border = WindowBorders.borders[win_id]

    if not border then
        -- Create new border if it doesn't exist
        border = create_border(win)
        WindowBorders.borders[win_id] = border
        return
    end

    -- Update border canvas frame (use max width for canvas)
    local frame = win:frame()
    local max_width = Config.borders.width_focused

    border:frame({
        x = frame.x - max_width,
        y = frame.y - max_width,
        w = frame.w + (max_width * 2),
        h = frame.h + (max_width * 2),
    })

    -- Update border rectangle frame
    border[1].frame = {
        x = max_width / 2,
        y = max_width / 2,
        w = frame.w + max_width,
        h = frame.h + max_width,
    }
end

-- Update border color and width based on focus and pin status
local function update_border_color(win, is_focused)
    if not win then return end

    local win_id = win:id()
    local border = WindowBorders.borders[win_id]
    if not border then return end

    local is_pinned = WindowManagement and WindowManagement.pinned_windows[win_id] ~= nil

    -- Select appropriate color and width
    local color_config
    local width
    if is_pinned then
        color_config = is_focused and Config.borders.pinned_focused or Config.borders.pinned_unfocused
        width = is_focused and Config.borders.width_focused or Config.borders.width_unfocused
    else
        color_config = is_focused and Config.borders.focused or Config.borders.unfocused
        width = is_focused and Config.borders.width_focused or Config.borders.width_unfocused
    end

    local fill_style = get_fill_style(color_config)

    -- Update border stroke color and width
    border[1].strokeColor = fill_style
    border[1].strokeWidth = width
end

-- Remove border for a window
local function remove_border(win_id)
    local border = WindowBorders.borders[win_id]
    if border then
        border:delete()
        WindowBorders.borders[win_id] = nil
    end
end

-- ============================================================================
-- Public API
-- ============================================================================

-- Draw/update border for a window
function WindowBorders.update_window(win)
    if not WindowBorders.enabled then return end
    if not win then return end

    -- Only draw borders for tileable windows
    if not WindowManagement.is_tileable(win) then
        remove_border(win:id())
        return
    end

    -- Skip borders on built-in display (no tiling there)
    local screen = win:screen()
    if screen and WindowManagement.is_builtin_screen then
        if WindowManagement.is_builtin_screen(screen) then
            remove_border(win:id())
            return
        end
    end

    update_border(win)
end

-- Update focus state for borders (only updates affected windows)
function WindowBorders.update_focus()
    if not WindowBorders.enabled then return end

    local focused_win = hs.window.focusedWindow()
    local focused_id = focused_win and focused_win:id()

    -- Skip if focus hasn't changed
    if focused_id == WindowBorders.last_focused_id then
        return
    end

    -- Update previously focused window to unfocused (if it exists and still has a border)
    if WindowBorders.last_focused_id then
        local prev_win = hs.window.find(WindowBorders.last_focused_id)
        if prev_win and WindowBorders.borders[WindowBorders.last_focused_id] then
            update_border_color(prev_win, false)
        end
    end

    -- Update newly focused window to focused
    if focused_win and WindowManagement and WindowManagement.is_tileable(focused_win) then
        -- Skip borders on built-in display (no tiling there)
        local screen = focused_win:screen()
        if screen and WindowManagement.is_builtin_screen and WindowManagement.is_builtin_screen(screen) then
            -- Don't create border, but ensure any existing border is removed
            if WindowBorders.borders[focused_id] then
                remove_border(focused_id)
            end
        else
            -- Create border if it doesn't exist
            if not WindowBorders.borders[focused_id] then
                WindowBorders.borders[focused_id] = create_border(focused_win)
            else
                -- Update existing border to focused
                update_border_color(focused_win, true)
            end
        end
    end

    -- Track new focused window
    WindowBorders.last_focused_id = focused_id
end

-- Update all borders for all tileable windows
function WindowBorders.update_all()
    if not WindowBorders.enabled then return end

    -- Clean up borders for windows that no longer exist
    local valid_win_ids = {}
    for _, win in ipairs(hs.window.allWindows()) do
        valid_win_ids[win:id()] = true
    end

    for win_id, _ in pairs(WindowBorders.borders) do
        if not valid_win_ids[win_id] then
            remove_border(win_id)
            -- Clear last_focused_id if it was removed
            if WindowBorders.last_focused_id == win_id then
                WindowBorders.last_focused_id = nil
            end
        end
    end

    -- Update/create borders for all tileable windows
    for _, win in ipairs(hs.window.allWindows()) do
        if WindowManagement.is_tileable(win) then
            WindowBorders.update_window(win)
        end
    end

    -- Update focus colors
    WindowBorders.update_focus()
end

-- Remove border for a specific window
function WindowBorders.remove_window(win_id)
    remove_border(win_id)
    -- Clear last_focused_id if this was the focused window
    if WindowBorders.last_focused_id == win_id then
        WindowBorders.last_focused_id = nil
    end
end

-- Hide all borders instantly (for space transitions)
function WindowBorders.hide_all()
    for win_id, border in pairs(WindowBorders.borders) do
        if border then
            border:hide()
        end
    end
end

-- Show all borders instantly (for space transitions)
function WindowBorders.show_all()
    for win_id, border in pairs(WindowBorders.borders) do
        if border then
            border:show()
        end
    end
end

-- ============================================================================
-- Module Control
-- ============================================================================

function WindowBorders.start()
    if WindowBorders.enabled then
        log.w("Window borders already enabled")
        return
    end

    log.i("Starting window borders")
    WindowBorders.enabled = true

    -- Draw initial borders
    WindowBorders.update_all()

    log.i("Window borders started")
end

function WindowBorders.stop()
    if not WindowBorders.enabled then
        log.w("Window borders already disabled")
        return
    end

    log.i("Stopping window borders")
    WindowBorders.enabled = false

    -- Remove all borders
    for win_id, _ in pairs(WindowBorders.borders) do
        remove_border(win_id)
    end

    log.i("Window borders stopped")
end

function WindowBorders.toggle()
    if WindowBorders.enabled then
        WindowBorders.stop()
        Helpers.alert("Borders disabled")
    else
        WindowBorders.start()
        Helpers.alert("Borders enabled")
    end
end

log.i("Window borders module loaded")

return WindowBorders
