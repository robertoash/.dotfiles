-- ============================================================================
-- Window Management Module
-- ============================================================================
-- Automatic tiling window management with intelligent layout selection
-- Replaces: Amethyst
--
-- Features:
-- - Auto-selects "tall" layout for horizontal (landscape) monitors
-- - Auto-selects "wide" layout for vertical (portrait) monitors
-- - Respects screen padding and window margins from Amethyst config
-- - Auto-retiles on window creation, close, and screen changes
-- ============================================================================

WindowManagement = WindowManagement or {}

local log = hs.logger.new('window-mgmt', 'info')

-- Load centralized config
local Config = require("config")

-- ============================================================================
-- Module State
-- ============================================================================

WindowManagement.config = {
    -- Enable/disable tiling
    enabled = true,
}

-- State
WindowManagement.watchers = {
    screen = nil,
    space = nil,
}

-- Window order tracking (per screen per space)
-- Structure: window_order[screen_id][space_id] = {win_id1, win_id2, ...}
WindowManagement.window_order = {}

-- Last master window per screen (for swap-with-master history)
WindowManagement.last_master = {}

-- Master factor (mfact) per screen - tracks the master window size ratio
-- Defaults to 0.65 (65%), but persists user manual adjustments
WindowManagement.screen_mfact = {}

-- Expected window frames after tiling (to detect manual resizing)
WindowManagement.expected_frames = {}

-- Flag to temporarily disable manual resize detection during programmatic changes
WindowManagement.ignore_resize_events = false

-- Flag to indicate we're in the middle of a space change (not a window move)
WindowManagement.space_change_in_progress = false

-- Set of window IDs currently being moved (excludes them from tiling)
-- Used for cross-space moves and can be extended for drag-and-drop reordering
WindowManagement.windows_being_moved = {}

-- Track previous screen for each window (to detect cross-monitor moves)
WindowManagement.window_previous_screen = {}

-- Pinned windows (appear on all spaces in same tiled position)
-- Maps window ID -> {screen_id, position_index}
WindowManagement.pinned_windows = {}

-- Per-screen tiling enabled state
-- Maps screen_id -> boolean (true = tiling enabled, false = tiling disabled but gap enforced)
-- Defaults: external screens = true, builtin = false
WindowManagement.screen_tiling_enabled = {}

-- ============================================================================
-- Screen Detection
-- ============================================================================

-- Check if screen is the built-in display (should be excluded from tiling)
local function is_builtin_screen(screen)
    if not screen then return false end
    local name = screen:name()
    -- Check if this is the built-in display
    return name and name:match("Built%-in") ~= nil
end

-- Public API for other modules
function WindowManagement.is_builtin_screen(screen)
    return is_builtin_screen(screen)
end

-- ============================================================================
-- Layout Detection
-- ============================================================================

-- Determine if screen is vertical (portrait) or horizontal (landscape)
local function is_screen_vertical(screen)
    local frame = screen:frame()
    return frame.h > frame.w
end

-- Get appropriate layout for screen
local function get_layout_for_screen(screen)
    if is_screen_vertical(screen) then
        return "wide"  -- Master top for portrait
    else
        return "tall"  -- Master left for landscape
    end
end

-- ============================================================================
-- Window Filtering
-- ============================================================================

-- Check if window is a proportional-tile app (tiles but maintains aspect ratio)
local function is_proportional_tile_app(win)
    if not win then return false end
    local app = win:application()
    if not app then return false end

    local app_name = app:name()
    for _, floating_app in ipairs(Config.window_rules.floating_apps) do
        if app_name == floating_app then
            return true
        end
    end
    return false
end

-- Check if window should be tiled (public API for other modules)
function WindowManagement.is_tileable(win)
    if not win then return false end

    -- Exclude windows currently being moved (cross-space or drag-and-drop)
    local win_id = nil
    pcall(function() win_id = win:id() end)
    if win_id and WindowManagement.windows_being_moved[win_id] then
        return false
    end

    if not win:isStandard() then return false end
    if not win:isVisible() then return false end
    if win:isFullScreen() then return false end

    -- All standard windows are now tileable (including former floating apps)
    return true
end

-- Get screen ID for tracking (public API for event modules)
function WindowManagement.get_screen_id(screen)
    return screen:id()
end

-- Private alias for internal use
local function get_screen_id(screen)
    return WindowManagement.get_screen_id(screen)
end

-- ============================================================================
-- Per-Screen Tiling Control
-- ============================================================================

-- Check if tiling is enabled for a specific screen
-- Returns true if tiling should be active, false if only gap enforcement
local function is_tiling_enabled(screen)
    if not screen then return false end
    local screen_id = get_screen_id(screen)

    -- If explicitly set, use that value
    if WindowManagement.screen_tiling_enabled[screen_id] ~= nil then
        return WindowManagement.screen_tiling_enabled[screen_id]
    end

    -- Default: external screens are tiled, builtin is not
    return not is_builtin_screen(screen)
end

-- Public API for checking tiling state
function WindowManagement.is_tiling_enabled(screen)
    return is_tiling_enabled(screen)
end

-- Set tiling enabled/disabled for a specific screen
local function set_tiling_enabled(screen, enabled)
    if not screen then return end
    local screen_id = get_screen_id(screen)
    WindowManagement.screen_tiling_enabled[screen_id] = enabled
    log.i(string.format("🔧 Screen %s tiling %s", screen:name(), enabled and "enabled" or "disabled"))
end

-- ============================================================================
-- Gap Enforcement for Untiled Screens
-- ============================================================================

-- Enforce top gap on untiled screens (prevents windows from overlapping menu bar space)
function WindowManagement.enforce_top_gap(win)
    if not win then return end

    local screen = win:screen()
    if not screen then return end

    -- Only enforce gap on untiled screens
    if is_tiling_enabled(screen) then return end

    -- Only enforce on standard, visible windows
    if not win:isStandard() or not win:isVisible() or win:isFullScreen() then
        return
    end

    local screen_frame = screen:frame()
    local win_frame = win:frame()

    -- Use builtin-specific gap for builtin displays, regular top padding for others
    local top_gap = is_builtin_screen(screen)
        and Config.layout.builtin_top_gap
        or Config.layout.padding.top

    -- Check if window's top edge is above the gap threshold
    local min_y = screen_frame.y + top_gap

    if win_frame.y < min_y then
        -- Window is encroaching into reserved space, push it down
        win_frame.y = min_y
        win:setFrame(win_frame, 0)
        log.d(string.format("⬇️  Enforced top gap (%dpx) on %s: pushed to y=%.0f", top_gap, win:title() or "unknown", min_y))
    end
end

-- Enforce top gap on all windows for a specific screen
local function enforce_gap_all_windows(screen)
    if not screen then return end
    if is_tiling_enabled(screen) then return end

    local all_windows = hs.window.allWindows()
    for _, win in ipairs(all_windows) do
        if win:screen() == screen then
            WindowManagement.enforce_top_gap(win)
        end
    end
    log.i(string.format("🔒 Enforced top gap on all windows for screen: %s", screen:name()))
end

-- Public API to enforce gap on all windows on all untiled screens
function WindowManagement.enforce_gap_all_screens()
    local screens = hs.screen.allScreens()
    for _, screen in ipairs(screens) do
        enforce_gap_all_windows(screen)
    end
end

-- Get current space ID for a screen
local function get_space_id(screen)
    -- Try to get space ID using hs.spaces
    local success, result = pcall(function()
        return hs.spaces.activeSpaceOnScreen(screen)
    end)

    if success and result then
        return tostring(result)
    end

    -- Fall back to "default" if hs.spaces not available
    return "default"
end

-- Get master factor for screen (defaults to config value if not set)
local function get_mfact(screen)
    local screen_id = get_screen_id(screen)
    local mfact = WindowManagement.screen_mfact[screen_id] or Config.layout.default_mfact
    log.d(string.format("get_mfact(screen=%s) = %.2f", screen_id, mfact))
    return mfact
end

-- Set master factor for screen
local function set_mfact(screen, mfact)
    local screen_id = get_screen_id(screen)
    -- Clamp mfact between configured limits
    WindowManagement.screen_mfact[screen_id] = math.max(Config.layout.mfact_min, math.min(Config.layout.mfact_max, mfact))
    log.f("Set mfact for screen to %.2f", WindowManagement.screen_mfact[screen_id])
end

-- Calculate usable screen frame (minus padding)
local function get_usable_frame(screen)
    local frame = screen:frame()
    local padding = Config.layout.padding

    return {
        x = frame.x + padding.left,
        y = frame.y + padding.top,
        w = frame.w - padding.left - padding.right,
        h = frame.h - padding.top - padding.bottom,
    }
end

-- Infer mfact and window order from current window layout (for cold start)
local function infer_layout_from_current_windows(screen, windows)
    if #windows <= 1 then return end

    local screen_id = get_screen_id(screen)
    local layout = get_layout_for_screen(screen)
    local frame = get_usable_frame(screen)

    -- Find the window that looks like the master (largest in the primary dimension)
    local master_candidate = nil
    local master_size = 0

    for _, win in ipairs(windows) do
        local win_frame = win:frame()
        local size = (layout == "tall") and win_frame.w or win_frame.h
        if size > master_size then
            master_size = size
            master_candidate = win
        end
    end

    if not master_candidate then return end

    -- Calculate mfact from master window size
    local master_frame = master_candidate:frame()
    local inferred_mfact
    local margin = Config.layout.margin

    if layout == "tall" then
        inferred_mfact = (master_frame.w + margin) / frame.w
    else
        inferred_mfact = (master_frame.h + margin) / frame.h
    end

    -- Only save if it looks reasonable (between 0.3 and 0.8)
    if inferred_mfact >= 0.3 and inferred_mfact <= 0.8 then
        set_mfact(screen, inferred_mfact)
        log.i(string.format("🔍 Inferred mfact=%.2f from existing layout", inferred_mfact))
    end

    -- Order windows: master first, then others by position
    local ordered = {}
    table.insert(ordered, master_candidate:id())

    -- Add remaining windows in spatial order
    local remaining = {}
    for _, win in ipairs(windows) do
        if win:id() ~= master_candidate:id() then
            table.insert(remaining, win)
        end
    end

    -- Sort remaining by position (Y for tall, X for wide)
    table.sort(remaining, function(a, b)
        local a_frame = a:frame()
        local b_frame = b:frame()
        if layout == "tall" then
            return a_frame.y < b_frame.y
        else
            return a_frame.x < b_frame.x
        end
    end)

    for _, win in ipairs(remaining) do
        table.insert(ordered, win:id())
    end

    -- Save inferred order (per screen per space)
    local space_id = get_space_id(screen)
    if not WindowManagement.window_order[screen_id] then
        WindowManagement.window_order[screen_id] = {}
    end
    WindowManagement.window_order[screen_id][space_id] = ordered
    log.i(string.format("🔍 Inferred window order: %d windows (screen=%s, space=%s)", #ordered, screen_id, space_id))
end

-- Initialize window order for screen+space if needed
local function ensure_window_order(screen)
    local screen_id = get_screen_id(screen)
    local space_id = get_space_id(screen)
    if not WindowManagement.window_order[screen_id] then
        WindowManagement.window_order[screen_id] = {}
    end
    if not WindowManagement.window_order[screen_id][space_id] then
        WindowManagement.window_order[screen_id][space_id] = {}
    end
end

-- Get tileable windows for a screen in tracked order
local function get_tileable_windows(screen)
    ensure_window_order(screen)
    local screen_id = get_screen_id(screen)
    local space_id = get_space_id(screen)
    local ordered_ids = WindowManagement.window_order[screen_id][space_id]

    log.d(string.format("🔍 Getting tileable windows for screen %s, space %s. Current order: [%s]",
        screen_id, space_id, table.concat(ordered_ids, ", ")))

    -- Get all current tileable windows ON THIS SPACE
    local current_windows = {}
    local current_ids = {}
    local all_windows = hs.window.allWindows()

    for _, win in ipairs(all_windows) do
        if WindowManagement.is_tileable(win) and win:screen() == screen then
            -- Check if window is on the current space
            local on_current_space = true
            local win_id = win:id()
            local win_spaces_str = "unknown"
            pcall(function()
                local win_spaces = hs.spaces.windowSpaces(win)
                if win_spaces and #win_spaces > 0 then
                    on_current_space = false
                    local spaces_list = {}
                    for _, ws in ipairs(win_spaces) do
                        table.insert(spaces_list, tostring(ws))
                        if tostring(ws) == space_id then
                            on_current_space = true
                        end
                    end
                    win_spaces_str = table.concat(spaces_list, ", ")
                end
            end)

            log.d(string.format("  Window %d: spaces=[%s], on_current_space=%s",
                win_id, win_spaces_str, tostring(on_current_space)))

            if on_current_space then
                local id = win:id()
                current_windows[id] = win
                table.insert(current_ids, id)

                -- Initialize screen tracking if not already set
                if not WindowManagement.window_previous_screen[id] then
                    WindowManagement.window_previous_screen[id] = screen
                    log.d(string.format("  Initialized screen tracking for window %d", id))
                end
            end
        end
    end

    log.d(string.format("  Found %d tileable windows on current space: [%s]",
        #current_ids, table.concat(current_ids, ", ")))

    -- If we have windows but no saved order, infer layout from current state
    if #current_ids > 0 and #ordered_ids == 0 then
        log.i(string.format("⚠️  No saved window order for screen %s, space %s - inferring from layout (this shouldn't happen on space return!)", screen_id, space_id))
        local windows_list = {}
        for _, id in ipairs(current_ids) do
            table.insert(windows_list, current_windows[id])
        end
        infer_layout_from_current_windows(screen, windows_list)
        -- Reload the ordered_ids after inference
        ordered_ids = WindowManagement.window_order[screen_id][space_id]
    else
        log.d(string.format("✓ Using saved window order: %d windows for screen %s, space %s", #ordered_ids, screen_id, space_id))
    end

    -- Build ordered list based on tracked order
    local result = {}
    local used = {}

    -- First, add windows in tracked order
    for _, id in ipairs(ordered_ids) do
        if current_windows[id] then
            table.insert(result, current_windows[id])
            used[id] = true
        end
    end

    -- Then add any new windows that aren't tracked yet
    for _, id in ipairs(current_ids) do
        if not used[id] then
            table.insert(result, current_windows[id])
        end
    end

    -- Update tracked order for this screen+space
    WindowManagement.window_order[screen_id][space_id] = {}
    for _, win in ipairs(result) do
        table.insert(WindowManagement.window_order[screen_id][space_id], win:id())
    end

    return result
end

-- ============================================================================
-- Layout Helpers
-- ============================================================================

-- Handle master window destruction - reset mfact if master is destroyed (public API for event modules)
function WindowManagement.handle_master_destroyed(win_id, screen)
    local screen_id = get_screen_id(screen)
    local space_id = get_space_id(screen)
    local order = WindowManagement.window_order[screen_id] and WindowManagement.window_order[screen_id][space_id]

    if not order or #order == 0 then return end

    -- Check if the destroyed window was the master
    if order[1] == win_id then
        -- Master window destroyed, reset mfact to default
        WindowManagement.screen_mfact[screen_id] = nil
        log.i("🔄 Master window destroyed, mfact reset to default (0.65)")
    end

    -- Clean up expected frame tracking
    WindowManagement.expected_frames[win_id] = nil
end

-- Detect manual resize of master window and update mfact (public API for event modules)
function WindowManagement.detect_manual_resize(win, screen)
    -- Skip detection if we're in the middle of programmatic changes
    if WindowManagement.ignore_resize_events then
        return false
    end

    if not WindowManagement.is_tileable(win) then return false end

    local windows = get_tileable_windows(screen)
    if #windows <= 1 then return false end

    -- Check if this is the master window
    local is_master = (windows[1]:id() == win:id())
    if not is_master then return false end

    -- Get expected and actual frames
    local expected = WindowManagement.expected_frames[win:id()]
    if not expected then return false end

    local actual = win:frame()

    -- Tolerance for frame comparison (5 pixels)
    local tolerance = 5

    -- Check if window was manually resized (frame differs from expected)
    local width_diff = math.abs(actual.w - expected.w)
    local height_diff = math.abs(actual.h - expected.h)

    if width_diff > tolerance or height_diff > tolerance then
        -- Master window was manually resized, calculate new mfact
        local frame = get_usable_frame(screen)
        local layout = get_layout_for_screen(screen)
        local margin = Config.layout.margin
        local new_mfact

        if layout == "tall" then
            -- Calculate mfact from actual master width
            new_mfact = (actual.w + margin) / frame.w
        else
            -- Calculate mfact from actual master height
            new_mfact = (actual.h + margin) / frame.h
        end

        -- Save new mfact
        set_mfact(screen, new_mfact)
        log.i(string.format("📐 Manual resize detected: master mfact updated to %.2f", new_mfact))
        return true
    end

    return false
end

-- Detect where a window was dropped and reorder accordingly (public API for event modules)
function WindowManagement.handle_window_drop(win, screen)
    if not WindowManagement.is_tileable(win) then return end

    ensure_window_order(screen)
    local screen_id = get_screen_id(screen)
    local windows = get_tileable_windows(screen)

    if #windows <= 1 then return end

    -- Get layout type and usable frame
    local layout = get_layout_for_screen(screen)
    local frame = get_usable_frame(screen)
    local win_frame = win:frame()
    local win_center_x = win_frame.x + win_frame.w / 2
    local win_center_y = win_frame.y + win_frame.h / 2

    -- Find window's current index
    local current_index = nil
    for i, w in ipairs(windows) do
        if w:id() == win:id() then
            current_index = i
            break
        end
    end

    if not current_index then return end

    local target_index = current_index

    local mfact = get_mfact(screen)

    if layout == "tall" then
        -- Tall layout: master on left (mfact%), stack on right (1-mfact%)
        local master_width = frame.w * mfact

        if win_center_x < frame.x + master_width then
            -- Dropped in master area
            target_index = 1
        else
            -- Dropped in stack area - determine position based on Y
            if #windows > 1 then
                local stack_height = frame.h / (#windows - 1)
                local relative_y = win_center_y - frame.y
                target_index = math.max(2, math.min(#windows, math.floor(relative_y / stack_height) + 2))
            end
        end
    else
        -- Wide layout: master on top (mfact%), stack on bottom (1-mfact%)
        local master_height = frame.h * mfact

        if win_center_y < frame.y + master_height then
            -- Dropped in master area
            target_index = 1
        else
            -- Dropped in stack area - determine position based on X
            if #windows > 1 then
                local stack_width = frame.w / (#windows - 1)
                local relative_x = win_center_x - frame.x
                target_index = math.max(2, math.min(#windows, math.floor(relative_x / stack_width) + 2))
            end
        end
    end

    -- Reorder if position changed
    if target_index ~= current_index then
        log.f("Reordering window from position %d to %d", current_index, target_index)

        local win_id = win:id()
        local space_id = get_space_id(screen)
        table.remove(WindowManagement.window_order[screen_id][space_id], current_index)
        table.insert(WindowManagement.window_order[screen_id][space_id], target_index, win_id)
    end
end

-- ============================================================================
-- Proportional Window Sizing
-- ============================================================================

-- Calculate proportional frame for windows that maintain aspect ratio
-- center_axis: "x", "y", or "both" - which axes to center on
local function calculate_proportional_frame(win, target_frame, center_axis)
    center_axis = center_axis or "none"

    -- Get window's current size to determine aspect ratio
    local current_frame = win:frame()
    local aspect_ratio = current_frame.w / current_frame.h

    -- Calculate maximum size that fits within target while maintaining aspect ratio
    local max_width = target_frame.w
    local max_height = target_frame.h

    local new_width, new_height

    -- Fit within bounds maintaining aspect ratio
    if max_width / aspect_ratio <= max_height then
        -- Width is the limiting factor
        new_width = max_width
        new_height = max_width / aspect_ratio
    else
        -- Height is the limiting factor
        new_height = max_height
        new_width = new_height * aspect_ratio
    end

    -- Calculate offsets based on centering preference
    local x_offset = 0
    local y_offset = 0

    if center_axis == "both" then
        x_offset = (target_frame.w - new_width) / 2
        y_offset = (target_frame.h - new_height) / 2
    elseif center_axis == "x" then
        x_offset = (target_frame.w - new_width) / 2
    elseif center_axis == "y" then
        y_offset = (target_frame.h - new_height) / 2
    end

    return {
        x = target_frame.x + x_offset,
        y = target_frame.y + y_offset,
        w = new_width,
        h = new_height,
    }
end

-- ============================================================================
-- Tiling Layouts
-- ============================================================================

-- Tall layout: Master on left, stack on right
local function apply_tall_layout(screen, windows)
    if #windows == 0 then return end

    local frame = get_usable_frame(screen)
    local margin = Config.layout.margin
    local mfact = get_mfact(screen)

    if #windows == 1 then
        -- Single window - full screen (minus padding)
        local target_frame = {
            x = frame.x,
            y = frame.y,
            w = frame.w,
            h = frame.h,
        }

        -- Check if window should maintain aspect ratio
        local win_frame
        if is_proportional_tile_app(windows[1]) then
            win_frame = calculate_proportional_frame(windows[1], target_frame, "both")
        else
            win_frame = target_frame
        end

        windows[1]:setFrame(win_frame, 0)
        -- Save expected frame
        WindowManagement.expected_frames[windows[1]:id()] = win_frame
    else
        -- Master on left (mfact%), stack on right (1-mfact%)
        local master_width = (frame.w * mfact) - margin
        local stack_width = (frame.w * (1 - mfact)) - margin

        -- Master window
        local master_target_frame = {
            x = frame.x,
            y = frame.y,
            w = master_width,
            h = frame.h,
        }

        local master_frame
        if is_proportional_tile_app(windows[1]) then
            master_frame = calculate_proportional_frame(windows[1], master_target_frame, "both")
        else
            master_frame = master_target_frame
        end

        windows[1]:setFrame(master_frame, 0)
        -- Save expected frame
        WindowManagement.expected_frames[windows[1]:id()] = master_frame

        -- Calculate available space for stack windows (accounting for gaps)
        local num_stack_windows = #windows - 1
        local total_margin_space = margin * (num_stack_windows - 1)
        local available_stack_height = frame.h - total_margin_space

        log.d(string.format("Stack layout: num=%d, total_margin=%.1f, available=%.1f",
            num_stack_windows, total_margin_space, available_stack_height))

        -- First pass: calculate all stack window heights
        local stack_frames = {}
        local total_stack_height = 0
        for i = 2, #windows do
            local stack_target_frame = {
                x = frame.x + master_width + (margin * 2),
                y = 0,  -- Will calculate later
                w = stack_width,
                h = available_stack_height / num_stack_windows,
            }

            local stack_frame
            if is_proportional_tile_app(windows[i]) then
                stack_frame = calculate_proportional_frame(windows[i], stack_target_frame, "none")
                log.d(string.format("Window %d (proportional): target_h=%.1f, actual_h=%.1f",
                    i, stack_target_frame.h, stack_frame.h))
            else
                stack_frame = stack_target_frame
                log.d(string.format("Window %d (regular): h=%.1f", i, stack_frame.h))
            end

            stack_frames[i] = stack_frame
            total_stack_height = total_stack_height + stack_frame.h
        end

        -- Calculate even gap between all stack windows based on unused space
        local unused_space = available_stack_height - total_stack_height
        local extra_gap = unused_space / num_stack_windows

        log.d(string.format("Gap calculation: unused=%.1f, extra_gap=%.1f, base_margin=%.1f, total_gap=%.1f",
            unused_space, extra_gap, margin, margin + extra_gap))

        -- Second pass: position windows with even gaps
        local current_y = frame.y
        for i = 2, #windows do
            stack_frames[i].y = current_y
            windows[i]:setFrame(stack_frames[i], 0)
            WindowManagement.expected_frames[windows[i]:id()] = stack_frames[i]
            log.d(string.format("Window %d positioned at y=%.1f, height=%.1f", i, current_y, stack_frames[i].h))
            current_y = current_y + stack_frames[i].h + margin + extra_gap
        end
    end

    log.f("Applied tall layout to %d windows on screen (mfact=%.2f)", #windows, mfact)
end

-- Wide layout: Master on top, stack on bottom
local function apply_wide_layout(screen, windows)
    if #windows == 0 then return end

    local frame = get_usable_frame(screen)
    local margin = Config.layout.margin
    local mfact = get_mfact(screen)

    if #windows == 1 then
        -- Single window - full screen (minus padding)
        local target_frame = {
            x = frame.x,
            y = frame.y,
            w = frame.w,
            h = frame.h,
        }

        -- Check if window should maintain aspect ratio
        local win_frame
        if is_proportional_tile_app(windows[1]) then
            win_frame = calculate_proportional_frame(windows[1], target_frame, "both")
        else
            win_frame = target_frame
        end

        windows[1]:setFrame(win_frame, 0)
        -- Save expected frame
        WindowManagement.expected_frames[windows[1]:id()] = win_frame
    else
        -- Master on top (mfact%), stack on bottom (1-mfact%)
        local master_height = (frame.h * mfact) - margin
        local stack_height = (frame.h * (1 - mfact)) - margin
        local stack_width = (frame.w - (margin * (#windows - 2))) / (#windows - 1)

        -- Master window
        local master_target_frame = {
            x = frame.x,
            y = frame.y,
            w = frame.w,
            h = master_height,
        }

        local master_frame
        if is_proportional_tile_app(windows[1]) then
            master_frame = calculate_proportional_frame(windows[1], master_target_frame, "both")
        else
            master_frame = master_target_frame
        end

        windows[1]:setFrame(master_frame, 0)
        -- Save expected frame
        WindowManagement.expected_frames[windows[1]:id()] = master_frame

        -- Calculate available space for stack windows (accounting for gaps)
        local num_stack_windows = #windows - 1
        local total_margin_space = margin * (num_stack_windows - 1)
        local available_stack_width = frame.w - total_margin_space

        log.d(string.format("Stack layout: num=%d, total_margin=%.1f, available=%.1f",
            num_stack_windows, total_margin_space, available_stack_width))

        -- First pass: calculate all stack window widths
        local stack_frames = {}
        local total_stack_width = 0
        for i = 2, #windows do
            local stack_target_frame = {
                x = 0,  -- Will calculate later
                y = frame.y + master_height + (margin * 2),
                w = available_stack_width / num_stack_windows,
                h = stack_height,
            }

            local stack_frame
            if is_proportional_tile_app(windows[i]) then
                stack_frame = calculate_proportional_frame(windows[i], stack_target_frame, "none")
                log.d(string.format("Window %d (proportional): target_w=%.1f, actual_w=%.1f",
                    i, stack_target_frame.w, stack_frame.w))
            else
                stack_frame = stack_target_frame
                log.d(string.format("Window %d (regular): w=%.1f", i, stack_frame.w))
            end

            stack_frames[i] = stack_frame
            total_stack_width = total_stack_width + stack_frame.w
        end

        -- Calculate even gap between all stack windows based on unused space
        local unused_space = available_stack_width - total_stack_width
        local extra_gap = unused_space / num_stack_windows

        log.d(string.format("Gap calculation: unused=%.1f, extra_gap=%.1f, base_margin=%.1f, total_gap=%.1f",
            unused_space, extra_gap, margin, margin + extra_gap))

        -- Second pass: position windows with even gaps
        local current_x = frame.x
        for i = 2, #windows do
            stack_frames[i].x = current_x
            windows[i]:setFrame(stack_frames[i], 0)
            WindowManagement.expected_frames[windows[i]:id()] = stack_frames[i]
            log.d(string.format("Window %d positioned at x=%.1f, width=%.1f", i, current_x, stack_frames[i].w))
            current_x = current_x + stack_frames[i].w + margin + extra_gap
        end
    end

    log.f("Applied wide layout to %d windows on screen (mfact=%.2f)", #windows, mfact)
end

-- ============================================================================
-- Tiling Engine
-- ============================================================================

-- Tile windows on a specific screen
function WindowManagement.tile_screen(screen)
    if not WindowManagement.config.enabled then return end

    -- Skip tiling on screens where it's disabled
    if not is_tiling_enabled(screen) then
        log.d(string.format("⏭️  Skipping tiling for screen: %s (tiling disabled)", screen:name()))
        return
    end

    local windows = get_tileable_windows(screen)
    if #windows == 0 then return end

    -- Suppress windowMoved events during programmatic repositioning
    WindowManagement.ignore_resize_events = true

    local layout = get_layout_for_screen(screen)

    log.i(string.format("🔧 TILING: %d windows on screen %s with %s layout", #windows, screen:name(), layout))

    if layout == "tall" then
        apply_tall_layout(screen, windows)
    else
        apply_wide_layout(screen, windows)
    end

    -- Update all borders after tiling to clean up any ghost borders
    if WindowBorders then
        WindowBorders.update_all()
    end

    -- Clear flag after a short delay to allow all positioning to complete
    hs.timer.doAfter(0.15, function()
        WindowManagement.ignore_resize_events = false
    end)
end

-- Tile all screens (only external monitors, excludes built-in display)
function WindowManagement.tile_all_screens()
    if not WindowManagement.config.enabled then return end

    local screens = hs.screen.allScreens()
    for _, screen in ipairs(screens) do
        -- tile_screen() already has built-in check, so this will skip it automatically
        WindowManagement.tile_screen(screen)
    end
end

-- ============================================================================
-- Window Navigation
-- ============================================================================

-- Focus next window on current screen
function WindowManagement.focus_next_window()
    local current = hs.window.focusedWindow()
    if not current then return end

    local screen = current:screen()

    -- Skip window navigation on untiled screens (no tiling order)
    if not is_tiling_enabled(screen) then return end

    local windows = get_tileable_windows(screen)

    if #windows <= 1 then return end

    -- Find current window index
    local current_index = nil
    for i, win in ipairs(windows) do
        if win:id() == current:id() then
            current_index = i
            break
        end
    end

    if current_index then
        -- Focus next window (wrap around)
        local next_index = (current_index % #windows) + 1
        windows[next_index]:focus()
        log.f("Focused next window: %s", windows[next_index]:title())
        -- Border update happens automatically via WindowFocusEvents
    end
end

-- Focus previous window on current screen
function WindowManagement.focus_prev_window()
    local current = hs.window.focusedWindow()
    if not current then return end

    local screen = current:screen()

    -- Skip window navigation on untiled screens (no tiling order)
    if not is_tiling_enabled(screen) then return end

    local windows = get_tileable_windows(screen)

    if #windows <= 1 then return end

    -- Find current window index
    local current_index = nil
    for i, win in ipairs(windows) do
        if win:id() == current:id() then
            current_index = i
            break
        end
    end

    if current_index then
        -- Focus previous window (wrap around)
        local prev_index = current_index == 1 and #windows or current_index - 1
        windows[prev_index]:focus()
        log.f("Focused previous window: %s", windows[prev_index]:title())
        -- Border update happens automatically via WindowFocusEvents
    end
end

-- Focus next screen (cycle through monitors)
function WindowManagement.focus_next_screen()
    -- Use focused window's screen, not mouse position
    local current_window = hs.window.focusedWindow()
    local current_screen = current_window and current_window:screen() or hs.mouse.getCurrentScreen()
    local next_screen = current_screen:next()
    local next_screen_id = get_screen_id(next_screen)
    local next_space_id = get_space_id(next_screen)

    -- Save current window focus before switching (using proper per-space tracking)
    if current_window and WindowManagement.is_tileable(current_window) and WindowFocusEvents then
        local current_screen_id = get_screen_id(current_screen)
        local current_space_id = get_space_id(current_screen)

        -- Initialize nested structure if needed
        if not WindowFocusEvents.last_focused[current_screen_id] then
            WindowFocusEvents.last_focused[current_screen_id] = {}
        end

        WindowFocusEvents.last_focused[current_screen_id][current_space_id] = current_window:id()
        log.i(string.format("💾 Saved current focus: %s (ID: %s) on screen %s, space %s",
            current_window:title(), current_window:id(), current_screen:name(), current_space_id))
    end

    -- Temporarily disable focus tracking to prevent intermediate focus events from overwriting last_focused
    if WindowFocusEvents then
        WindowFocusEvents.ignore_focus_events = true
    end

    -- Try to focus the last focused window on next screen's current space
    local last_focused_id = WindowFocusEvents.get_last_focused(next_screen_id, next_space_id)
    log.i(string.format("🔍 Monitor switch: next_screen_id=%s, next_space_id=%s, last_focused_id=%s",
        next_screen_id, next_space_id, last_focused_id or "nil"))

    if last_focused_id then
        local last_window = hs.window.find(last_focused_id)
        if last_window and WindowManagement.is_tileable(last_window) and last_window:screen() == next_screen then
            log.i(string.format("✅ Focusing last window: %s (ID: %s)", last_window:title(), last_focused_id))
            last_window:focus()
            log.f("Focused last used window on screen: %s", next_screen:name())
            -- Re-enable focus tracking immediately - border update via WindowFocusEvents
            if WindowFocusEvents then
                WindowFocusEvents.ignore_focus_events = false
            end
            return
        end
    end

    -- Fall back to first window on next screen
    local windows = get_tileable_windows(next_screen)
    if #windows > 0 then
        windows[1]:focus()
        log.f("Focused first window on screen: %s", next_screen:name())
        -- Re-enable focus tracking immediately - border update via WindowFocusEvents
        if WindowFocusEvents then
            WindowFocusEvents.ignore_focus_events = false
        end
    else
        -- No windows on next screen, just move mouse
        local frame = next_screen:frame()
        hs.mouse.absolutePosition({
            x = frame.x + frame.w / 2,
            y = frame.y + frame.h / 2
        })
        log.f("Moved mouse to screen: %s (no windows)", next_screen:name())
        -- Re-enable focus tracking immediately since no focus change happened
        if WindowFocusEvents then
            WindowFocusEvents.ignore_focus_events = false
        end
    end
end

-- Focus window by index on current screen (1=master, 2+=stack in layout order)
function WindowManagement.focus_window_by_index(index)
    local current = hs.window.focusedWindow()
    if not current then return end

    local screen = current:screen()

    -- Skip window navigation on untiled screens (no tiling order)
    if not is_tiling_enabled(screen) then return end

    local windows = get_tileable_windows(screen)

    if #windows == 0 then return end

    -- Clamp index to available windows (if requesting index 4 but only 2 windows, focus window 2)
    local target_index = math.min(index, #windows)
    windows[target_index]:focus()
    log.f("Focused window at index %d: %s", target_index, windows[target_index]:title())
    -- Border update happens automatically via WindowFocusEvents
end

-- Increase master factor (make master larger)
function WindowManagement.increase_mfact()
    local current = hs.window.focusedWindow()
    if not current then return end

    local screen = current:screen()

    -- Skip mfact adjustment on untiled screens (no tiling)
    if not is_tiling_enabled(screen) then return end

    local windows = get_tileable_windows(screen)

    if #windows <= 1 then
        Notifications.error("Need 2+ windows", 1.0)
        return
    end

    local current_mfact = get_mfact(screen)
    local new_mfact = math.min(Config.layout.mfact_max, current_mfact + Config.layout.mfact_step)

    if new_mfact == current_mfact then
        Notifications.error(string.format("Max size (%d%%)", Config.layout.mfact_max * 100), 1.0)
        return
    end

    -- Ignore resize events during programmatic adjustment
    WindowManagement.ignore_resize_events = true
    set_mfact(screen, new_mfact)
    WindowManagement.tile_screen(screen)
    -- Clear flag after windows have settled
    hs.timer.doAfter(1.0, function()
        WindowManagement.ignore_resize_events = false
    end)
    Notifications.toast(string.format("Master: %d%%", math.floor(new_mfact * 100)), 0.5)
end

-- Decrease master factor (make master smaller)
function WindowManagement.decrease_mfact()
    local current = hs.window.focusedWindow()
    if not current then return end

    local screen = current:screen()

    -- Skip mfact adjustment on untiled screens (no tiling)
    if not is_tiling_enabled(screen) then return end

    local windows = get_tileable_windows(screen)

    if #windows <= 1 then
        Notifications.error("Need 2+ windows", 1.0)
        return
    end

    local current_mfact = get_mfact(screen)
    local new_mfact = math.max(Config.layout.mfact_min, current_mfact - Config.layout.mfact_step)

    if new_mfact == current_mfact then
        Notifications.error(string.format("Min size (%d%%)", Config.layout.mfact_min * 100), 1.0)
        return
    end

    -- Ignore resize events during programmatic adjustment
    WindowManagement.ignore_resize_events = true
    set_mfact(screen, new_mfact)
    WindowManagement.tile_screen(screen)
    -- Clear flag after windows have settled
    hs.timer.doAfter(1.0, function()
        WindowManagement.ignore_resize_events = false
    end)
    Notifications.toast(string.format("Master: %d%%", math.floor(new_mfact * 100)), 0.5)
end

-- Swap active window with master, or swap master with last master
function WindowManagement.swap_with_master()
    local current = hs.window.focusedWindow()
    if not current or not WindowManagement.is_tileable(current) then
        log.w("No tileable window focused")
        Notifications.error("No tileable window focused", 1.0)
        return
    end

    local screen = current:screen()

    -- Skip swap on untiled screens (no tiling order)
    if not is_tiling_enabled(screen) then return end

    local screen_id = get_screen_id(screen)
    local windows = get_tileable_windows(screen)

    if #windows <= 1 then
        log.w("Only one window on screen, nothing to swap")
        Notifications.error("Only 1 window on monitor", 1.0)
        return
    end

    ensure_window_order(screen)
    local space_id = get_space_id(screen)
    local order = WindowManagement.window_order[screen_id][space_id]

    -- Find current window index
    local current_index = nil
    for i, id in ipairs(order) do
        if id == current:id() then
            current_index = i
            break
        end
    end

    if not current_index then
        log.w("Current window not found in tracked order")
        return
    end

    if current_index == 1 then
        -- Current is master - swap with last master if exists
        local last_master_id = WindowManagement.last_master[screen_id]
        local target_index = nil

        -- Try to find last master in current window list
        if last_master_id then
            for i, id in ipairs(order) do
                if id == last_master_id then
                    target_index = i
                    break
                end
            end
        end

        -- Fall back to first child if last master not found
        if not target_index or target_index == 1 then
            target_index = 2
        end

        -- Swap positions
        order[1], order[target_index] = order[target_index], order[1]
        log.f("Swapped master with window at index %d", target_index)
    else
        -- Current is not master - save current master and swap with it
        WindowManagement.last_master[screen_id] = order[1]
        order[1], order[current_index] = order[current_index], order[1]
        log.f("Swapped window at index %d with master", current_index)
    end

    -- Retile and focus the window that's now in master position
    WindowManagement.tile_screen(screen)
    hs.window.find(order[1]):focus()
end

-- ============================================================================
-- Pinned Windows (Appear on All Spaces)
-- ============================================================================

-- Pin current window (will follow to all spaces)
function WindowManagement.pin_window()
    local win = hs.window.focusedWindow()
    if not win or not WindowManagement.is_tileable(win) then
        Notifications.error("No tileable window focused", 1.0)
        return
    end

    local screen = win:screen()

    -- Skip pinning on untiled screens (no tiling position to preserve)
    if not is_tiling_enabled(screen) then return end

    local win_id = win:id()
    local screen_id = get_screen_id(screen)
    local windows = get_tileable_windows(screen)

    -- Find window's position in tiling order
    local position = nil
    for i, w in ipairs(windows) do
        if w:id() == win_id then
            position = i
            break
        end
    end

    if not position then
        Notifications.error("Window not found in tiling order", 1.0)
        return
    end

    WindowManagement.pinned_windows[win_id] = {
        screen_id = screen_id,
        position = position,
    }

    log.i(string.format("📌 Pinned window: %s (position %d)", win:title() or "unknown", position))
    Notifications.toast(string.format("📌 Pinned: %s", win:application():name()), 1.0)

    -- Update border to show pinned color
    if WindowBorders then
        WindowBorders.update_window(win)
    end
end

-- Unpin current window
function WindowManagement.unpin_window()
    local win = hs.window.focusedWindow()
    if not win then
        Notifications.error("No window focused", 1.0)
        return
    end

    local win_id = win:id()
    if not WindowManagement.pinned_windows[win_id] then
        Notifications.error("Window is not pinned", 1.0)
        return
    end

    WindowManagement.pinned_windows[win_id] = nil
    log.i(string.format("📍 Unpinned window: %s", win:title() or "unknown"))
    Notifications.toast(string.format("📍 Unpinned: %s", win:application():name()), 1.0)

    -- Update border to show normal color
    if WindowBorders then
        WindowBorders.update_window(win)
    end
end

-- Toggle pin on current window
function WindowManagement.toggle_pin()
    local win = hs.window.focusedWindow()
    if not win then return end

    if WindowManagement.pinned_windows[win:id()] then
        WindowManagement.unpin_window()
    else
        WindowManagement.pin_window()
    end
end

-- ============================================================================
-- Space Change Handler
-- ============================================================================

-- Move pinned windows to new space when switching
local function on_space_change()
    log.i("🌌 SPACE CHANGE DETECTED")

    -- Set flag to indicate space change (not window move)
    WindowManagement.space_change_in_progress = true

    -- Immediately disable borders to prevent flicker during space transition
    if WindowBorders then
        WindowBorders.enabled = false
    end

    -- Short delay to let space switch complete
    hs.timer.doAfter(0.2, function()
        -- Check if hs.spaces is available (has compatibility issues on some macOS versions)
        local success, spaces_module = pcall(function() return hs.spaces end)
        if not success or not spaces_module then
            log.w("hs.spaces not available, pinned windows won't move between spaces")
            -- Re-enable borders and clear flag before returning
            if WindowBorders then
                WindowBorders.enabled = true
                WindowBorders.show_all()
                WindowBorders.update_all()
            end
            WindowManagement.space_change_in_progress = false
            return
        end

        -- Get current space
        local current_space = spaces_module.focusedSpace()
        if not current_space then
            log.w("Could not get current space")
            -- Re-enable borders and clear flag before returning
            if WindowBorders then
                WindowBorders.enabled = true
                WindowBorders.show_all()
                WindowBorders.update_all()
            end
            WindowManagement.space_change_in_progress = false
            return
        end

        log.i(string.format("🌌 Switched to space: %s", tostring(current_space)))

        -- Check if current space is a fullscreen space (skip moving pinned windows but focus the fullscreen window)
        local space_type = spaces_module.spaceType(current_space)
        if space_type == "fullscreen" then
            log.i("Switched to fullscreen space, focusing fullscreen window")

            -- Find and focus the fullscreen window on this space
            local all_windows = hs.window.allWindows()
            for _, win in ipairs(all_windows) do
                if win:isFullScreen() and win:screen() == hs.screen.mainScreen() then
                    win:focus()
                    log.i(string.format("✅ Focused fullscreen window: %s", win:title()))
                    break
                end
            end

            -- Re-enable borders and clear flag before returning (fullscreen windows don't show borders anyway)
            if WindowBorders then
                WindowBorders.enabled = true
                WindowBorders.update_all()
            end
            WindowManagement.space_change_in_progress = false
            return
        end

        -- Move each pinned window to current space
        for win_id, pin_info in pairs(WindowManagement.pinned_windows) do
            local win = hs.window.find(win_id)
            if win then
                -- Check if window is already on this space
                local win_spaces = spaces_module.windowSpaces(win)
                local already_on_space = false
                if win_spaces then
                    for _, space_id in ipairs(win_spaces) do
                        if space_id == current_space then
                            already_on_space = true
                            break
                        end
                    end
                end

                if not already_on_space then
                    -- Move window to current space
                    local move_success = pcall(function()
                        spaces_module.moveWindowToSpace(win, current_space)
                    end)

                    if move_success then
                        log.i(string.format("📌 Moved pinned window to current space: %s", win:title() or "unknown"))
                    else
                        log.w(string.format("Failed to move pinned window: %s", win:title() or "unknown"))
                    end
                end
            else
                -- Window no longer exists, remove from pinned list
                WindowManagement.pinned_windows[win_id] = nil
                log.i(string.format("Removed stale pinned window: %d", win_id))
            end
        end

        -- Retile only the screen where the space changed (not all screens)
        -- Get the screen associated with this space change
        local current_screen = nil
        pcall(function()
            -- Try to get the screen for the current space
            for _, screen in ipairs(hs.screen.allScreens()) do
                local screen_space = spaces_module.activeSpaceOnScreen(screen)
                if screen_space == current_space then
                    current_screen = screen
                    break
                end
            end
        end)

        -- Fall back to main screen if we couldn't determine which screen changed
        if not current_screen then
            current_screen = hs.screen.mainScreen()
        end

        -- Retile only the affected screen (preserving existing window order)
        WindowManagement.tile_screen(current_screen)

        -- Restore focus to last focused window on current screen and space
        if WindowFocusEvents then
            local current_screen_id = get_screen_id(current_screen)
            local space_id_str = tostring(current_space)
            local last_focused_id = WindowFocusEvents.get_last_focused(current_screen_id, space_id_str)

            log.i(string.format("🔍 Space change focus restore: screen_id=%s, space_id=%s, last_focused_id=%s",
                current_screen_id, space_id_str, last_focused_id or "nil"))

            local window_to_focus = nil

            if last_focused_id then
                local last_window = hs.window.find(last_focused_id)
                if last_window and WindowManagement.is_tileable(last_window) and last_window:screen() == current_screen then
                    -- Verify window is still on current space (it should be from our per-space tracking)
                    local on_current_space = false
                    pcall(function()
                        local win_spaces = spaces_module.windowSpaces(last_window)
                        if win_spaces and #win_spaces > 0 then
                            for _, ws in ipairs(win_spaces) do
                                if ws == current_space then
                                    on_current_space = true
                                    break
                                end
                            end
                        end
                    end)

                    if on_current_space then
                        window_to_focus = last_window
                    else
                        log.i(string.format("Last focused window no longer on current space: %s", last_window:title()))
                    end
                else
                    log.i(string.format("Last focused window not found or not tileable (ID: %s)", last_focused_id))
                end
            else
                log.i(string.format("No last focused window for screen %s, space %s - will focus master", current_screen_id, space_id_str))
            end

            -- If no last focused window, fall back to master (first window in order)
            if not window_to_focus then
                local windows = get_tileable_windows(current_screen)
                if #windows > 0 then
                    window_to_focus = windows[1]
                    log.i(string.format("📍 Falling back to master window: %s", window_to_focus:title()))
                end
            end

            -- Focus the selected window
            if window_to_focus then
                -- Temporarily disable focus tracking to prevent this programmatic focus from being logged
                if WindowFocusEvents then
                    WindowFocusEvents.ignore_focus_events = true
                end

                window_to_focus:focus()
                log.i(string.format("✅ Focused window after space change: %s", window_to_focus:title()))

                -- Re-enable focus tracking immediately (no delay needed since we're already in delayed callback)
                if WindowFocusEvents then
                    WindowFocusEvents.ignore_focus_events = false
                end

                -- Re-enable borders and update focus (will show correct focused window)
                if WindowBorders then
                    WindowBorders.enabled = true
                    WindowBorders.show_all()
                    WindowBorders.update_focus()
                end
            else
                -- No window to focus, just re-enable borders
                if WindowBorders then
                    WindowBorders.enabled = true
                    WindowBorders.show_all()
                    WindowBorders.update_all()
                end
            end
        end

        -- Clear flag after space change completes
        WindowManagement.space_change_in_progress = false
    end)
end

-- ============================================================================
-- Screen Change Handler
-- ============================================================================

-- Screen layout change handler
local function on_screen_change()
    log.i("Screen layout changed, retiling all screens")
    hs.timer.doAfter(0.5, WindowManagement.tile_all_screens)
end

-- ============================================================================
-- Screen-Specific Tiling Toggle
-- ============================================================================

-- Toggle tiling on/off for current screen
function WindowManagement.toggle_screen_tiling()
    local current = hs.window.focusedWindow()
    if not current then
        -- No focused window, use mouse screen
        local screen = hs.mouse.getCurrentScreen()
        local current_state = is_tiling_enabled(screen)
        set_tiling_enabled(screen, not current_state)

        if not current_state then
            -- Just enabled tiling, tile the screen
            WindowManagement.tile_screen(screen)
            Notifications.toast(string.format("✅ Tiling enabled: %s", screen:name()), 2.0)
        else
            -- Just disabled tiling, show notification
            Notifications.toast(string.format("🚫 Tiling disabled: %s", screen:name()), 2.0)
        end
        return
    end

    local screen = current:screen()
    local current_state = is_tiling_enabled(screen)
    set_tiling_enabled(screen, not current_state)

    if not current_state then
        -- Just enabled tiling, tile the screen
        WindowManagement.tile_screen(screen)
        Notifications.toast(string.format("✅ Tiling enabled: %s", screen:name()), 2.0)
    else
        -- Just disabled tiling (gap enforcement will still apply)
        Notifications.toast(string.format("🚫 Tiling disabled: %s", screen:name()), 2.0)
    end
end

-- ============================================================================
-- Module Control
-- ============================================================================

-- Start window management
function WindowManagement.start()
    if WindowManagement.watchers.screen then
        log.w("Window management already started")
        return
    end

    log.i("Starting window management")

    -- Load and start event modules
    require("modules.window-events.focus")
    require("modules.window-events.structural")
    require("modules.window-borders")

    WindowFocusEvents.start()
    WindowStructuralEvents.start()
    WindowBorders.start()

    -- Watch for screen changes
    WindowManagement.watchers.screen = hs.screen.watcher.new(on_screen_change)
    WindowManagement.watchers.screen:start()

    -- Watch for space changes (for pinned windows and focus restoration)
    local spaces_success, spaces_watcher = pcall(function()
        return hs.spaces.watcher.new(on_space_change)
    end)

    if spaces_success and spaces_watcher then
        WindowManagement.watchers.space = spaces_watcher
        WindowManagement.watchers.space:start()
        log.i("✅ Space watcher started successfully (for pinned windows and focus restoration)")
    else
        log.w("❌ Failed to start space watcher (hs.spaces compatibility issue) - pinned windows won't move between spaces")
        log.w(string.format("Error: %s", tostring(spaces_watcher)))
    end

    -- Initial tiling
    WindowManagement.tile_all_screens()

    log.i("Window management started")
end

-- Stop window management
function WindowManagement.stop()
    log.i("Stopping window management")

    -- Stop event modules
    if WindowFocusEvents then
        WindowFocusEvents.stop()
    end

    if WindowStructuralEvents then
        WindowStructuralEvents.stop()
    end

    if WindowBorders then
        WindowBorders.stop()
    end

    if WindowManagement.watchers.screen then
        WindowManagement.watchers.screen:stop()
        WindowManagement.watchers.screen = nil
    end

    if WindowManagement.watchers.space then
        WindowManagement.watchers.space:stop()
        WindowManagement.watchers.space = nil
    end

    log.i("Window management stopped")
end

-- Toggle window management
function WindowManagement.toggle()
    WindowManagement.config.enabled = not WindowManagement.config.enabled

    if WindowManagement.config.enabled then
        Helpers.alert("Tiling enabled")
        WindowManagement.tile_all_screens()
    else
        Helpers.alert("Tiling disabled")
    end
end

-- ============================================================================
-- Auto-start
-- ============================================================================

if WindowManagement.config.enabled then
    WindowManagement.start()
end

log.i("Window management module loaded")

return WindowManagement
