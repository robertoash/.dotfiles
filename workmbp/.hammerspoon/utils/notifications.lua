-- ============================================================================
-- Notifications Module
-- ============================================================================
-- Custom toast notification system with stacking and animations
-- ============================================================================

Notifications = Notifications or {}

local log = hs.logger.new('notifications', 'info')

-- ============================================================================
-- Configuration
-- ============================================================================

local config = {
    -- Position (bottom of toast at 10% screen height)
    bottom_margin = 0.10,  -- 10% from bottom of screen

    -- Toast appearance
    width = 400,
    min_height = 50,
    padding = 16,
    corner_radius = 8,

    -- Colors
    bg_color = { red = 0.004, green = 0.004, blue = 0.067, alpha = 0.95 },  -- #010111
    text_color = { red = 1, green = 1, blue = 1, alpha = 1 },  -- White
    error_bg_color = { red = 1, green = 0.373, blue = 0.561, alpha = 0.95 },  -- #ff5f8f
    error_text_color = { red = 0.004, green = 0.004, blue = 0.067, alpha = 1 },  -- #010111

    -- Font
    font = "GeistMono Nerd Font",
    font_size = 15,

    -- Timing
    default_duration = 1.0,
    fade_duration = 0.15,
    slide_duration = 0.2,

    -- Stacking
    stack_spacing = 10,  -- Gap between toasts
}

-- ============================================================================
-- State
-- ============================================================================

-- Active toasts (array of toast objects)
local active_toasts = {}

-- ============================================================================
-- Toast Object
-- ============================================================================

local function create_toast(message, duration, is_error)
    duration = duration or config.default_duration
    is_error = is_error or false

    local screen = hs.mouse.getCurrentScreen()
    local screen_frame = screen:frame()

    -- Calculate toast height based on message length and line breaks
    local text_style = {
        font = { name = config.font, size = config.font_size },
        color = is_error and config.error_text_color or config.text_color,
        paragraphStyle = { alignment = "center" },
    }

    -- Estimate height based on line count (simple approach)
    local line_count = 1
    for _ in message:gmatch("\n") do
        line_count = line_count + 1
    end
    local estimated_height = (line_count * config.font_size * 1.5) + config.padding * 2
    local toast_height = math.max(config.min_height, estimated_height)

    -- Calculate initial position (off screen, below)
    local x = screen_frame.x + (screen_frame.w - config.width) / 2
    local target_y = screen_frame.y + screen_frame.h * (1 - config.bottom_margin) - toast_height
    local start_y = screen_frame.y + screen_frame.h + 10  -- Start below screen

    -- Create canvas
    local canvas = hs.canvas.new({
        x = x,
        y = start_y,
        w = config.width,
        h = toast_height,
    })

    -- Background
    canvas[1] = {
        type = "rectangle",
        action = "fill",
        fillColor = is_error and config.error_bg_color or config.bg_color,
        roundedRectRadii = { xRadius = config.corner_radius, yRadius = config.corner_radius },
    }

    -- Text
    canvas[2] = {
        type = "text",
        text = hs.styledtext.new(message, text_style),
        frame = {
            x = config.padding,
            y = config.padding,
            w = config.width - config.padding * 2,
            h = toast_height - config.padding * 2,
        },
    }

    local toast = {
        canvas = canvas,
        message = message,
        height = toast_height,
        target_y = target_y,
        current_y = start_y,
        screen = screen,
        timer = nil,
        is_error = is_error,
    }

    return toast
end

-- ============================================================================
-- Toast Management
-- ============================================================================

-- Update positions of all toasts (stack from bottom up)
local function update_toast_positions()
    if #active_toasts == 0 then return end

    -- Calculate target positions from bottom up
    local screen = hs.mouse.getCurrentScreen()
    local screen_frame = screen:frame()
    local bottom_y = screen_frame.y + screen_frame.h * (1 - config.bottom_margin)

    for i = 1, #active_toasts do
        local toast = active_toasts[i]
        local new_target_y = bottom_y - toast.height

        -- Account for toasts below this one
        for j = 1, i - 1 do
            new_target_y = new_target_y - active_toasts[j].height - config.stack_spacing
        end

        toast.target_y = new_target_y
    end
end

-- Animate toast to target position
local function animate_toast_to_target(toast)
    local frame = toast.canvas:frame()

    -- Animate with hs.timer for smooth movement
    local steps = 15
    local step_duration = config.slide_duration / steps
    local start_y = frame.y
    local delta_y = toast.target_y - start_y
    local step = 0

    local animation_timer = hs.timer.doEvery(step_duration, function()
        step = step + 1
        if step >= steps then
            frame.y = toast.target_y
            toast.canvas:frame(frame)
            toast.current_y = toast.target_y
            return false  -- Stop timer
        end

        -- Ease out animation
        local progress = step / steps
        local eased = 1 - math.pow(1 - progress, 3)
        frame.y = start_y + delta_y * eased
        toast.canvas:frame(frame)
        toast.current_y = frame.y
    end)

    return animation_timer
end

-- Show a toast
local function show_toast_internal(toast)
    -- Add to active toasts
    table.insert(active_toasts, toast)

    -- Update all positions
    update_toast_positions()

    -- Show canvas with fade in
    toast.canvas:alpha(0)
    toast.canvas:show()

    -- Fade in animation
    local fade_steps = 10
    local fade_step_duration = config.fade_duration / fade_steps
    local step = 0

    local fade_timer = hs.timer.doEvery(fade_step_duration, function()
        step = step + 1
        if step >= fade_steps then
            toast.canvas:alpha(1)
            return false  -- Stop timer
        end
        toast.canvas:alpha(step / fade_steps)
    end)
    fade_timer:start()

    -- Animate to target position
    hs.timer.doAfter(0.01, function()
        animate_toast_to_target(toast)
    end)

    -- Also animate other toasts to their new positions
    for i = 1, #active_toasts - 1 do
        animate_toast_to_target(active_toasts[i])
    end
end

-- Remove a toast
local function remove_toast(toast)
    -- Find toast index
    local index = nil
    for i, t in ipairs(active_toasts) do
        if t == toast then
            index = i
            break
        end
    end

    if not index then return end

    -- Fade out animation
    local fade_steps = 10
    local fade_step_duration = config.fade_duration / fade_steps
    local step = fade_steps

    local fade_timer = hs.timer.doEvery(fade_step_duration, function()
        step = step - 1
        if step <= 0 then
            toast.canvas:alpha(0)
            toast.canvas:delete()
            return false  -- Stop timer
        end
        toast.canvas:alpha(step / fade_steps)
    end)
    fade_timer:start()

    -- Remove from active toasts
    table.remove(active_toasts, index)

    -- Wait for fade animation to complete before shifting stack
    hs.timer.doAfter(config.fade_duration + 0.25, function()
        -- Update positions of remaining toasts
        update_toast_positions()

        -- Animate remaining toasts to new positions
        for _, t in ipairs(active_toasts) do
            animate_toast_to_target(t)
        end
    end)

    -- Cancel timer if exists
    if toast.timer then
        toast.timer:stop()
    end
end

-- ============================================================================
-- Public API
-- ============================================================================

-- Show a toast notification
function Notifications.toast(message, duration, is_error)
    duration = duration or config.default_duration
    is_error = is_error or false

    log.d(string.format("Showing toast: %s (error: %s)", message, tostring(is_error)))

    local toast = create_toast(message, duration, is_error)
    show_toast_internal(toast)

    -- Schedule removal
    toast.timer = hs.timer.doAfter(duration, function()
        remove_toast(toast)
    end)
end

-- Show error toast (red background)
function Notifications.error(message, duration)
    Notifications.toast(message, duration, true)
end

-- Clear all toasts
function Notifications.clear_all()
    for _, toast in ipairs(active_toasts) do
        if toast.timer then
            toast.timer:stop()
        end
        toast.canvas:delete()
    end
    active_toasts = {}
end

-- ============================================================================
-- Backward Compatibility (for existing code using Helpers.toast)
-- ============================================================================

-- Update Helpers to use new notification system
if Helpers then
    Helpers.toast = Notifications.toast
    Helpers.alert = Notifications.toast
    Helpers.error = Notifications.error
end

log.i("Notifications module loaded")

return Notifications
