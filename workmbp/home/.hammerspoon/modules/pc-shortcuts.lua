-- ============================================================================
-- PC Shortcuts Module
-- ============================================================================
-- Maps PC-style shortcuts to macOS equivalents using eventtap
-- Intelligently passes through Ctrl keys to terminals and other apps
-- ============================================================================

PcShortcuts = PcShortcuts or {}

local log = hs.logger.new('pc-shortcuts', 'info')

-- ============================================================================
-- Configuration
-- ============================================================================

PcShortcuts.config = {
    enabled = true,

    -- Patterns to match apps where Ctrl should pass through (case-insensitive)
    -- Uses Lua patterns: ^ = start of string, . = any char, etc.
    ctrl_passthrough_patterns = {
        "^wezterm",   -- Matches WezTerm, wezterm-gui, wezterm, etc.
        "^kitty",
        "^alacritty",
        "^iterm",     -- Matches iTerm2, iTerm, etc.
        "^terminal",
        "^neovide",
    },
}

-- State
PcShortcuts.eventtap = nil

-- ============================================================================
-- Key Mappings
-- ============================================================================

-- Keys that should be mapped from Ctrl to Cmd (by keyCode name)
-- These are common shortcuts that work in most apps
local ctrl_to_cmd_keys = {
    -- Editing
    "c", "v", "x", "z", "y", "a",
    -- File operations
    "s", "n", "o", "w", "p",
    -- Search and navigation
    "f", "g", "h", "l",
    -- Tabs and windows
    "t", "r",
    -- Text formatting
    "b", "i", "u", "k",
    -- Misc
    "d", "m",
    -- Brackets
    "[", "]",
}

-- Convert to set for faster lookup
local ctrl_to_cmd_set = {}
for _, key in ipairs(ctrl_to_cmd_keys) do
    ctrl_to_cmd_set[key] = true
end

-- ============================================================================
-- App Detection
-- ============================================================================

-- Check if current app should get real Ctrl keys
local function should_passthrough_ctrl()
    local app = hs.application.frontmostApplication()
    if not app then
        log.i("No frontmost app found")
        return false
    end

    local app_name = app:name()
    local app_name_lower = app_name:lower()  -- Case-insensitive matching
    log.i("Checking passthrough for app: \"" .. app_name .. "\"")

    for _, pattern in ipairs(PcShortcuts.config.ctrl_passthrough_patterns) do
        log.i("  Checking pattern: \"" .. pattern .. "\"")
        if app_name_lower:find(pattern) then
            log.i("  ✓ MATCH! Passing through Ctrl to " .. app_name)
            return true
        end
    end

    log.i("  ✗ No match, will remap")
    return false
end

-- ============================================================================
-- Event Handler
-- ============================================================================

local function handle_key_event(event)
    local flags = event:getFlags()
    local keyCode = event:getKeyCode()

    -- Get the key character from the key code
    local keyChar = hs.keycodes.map[keyCode]
    if not keyChar then
        return false  -- Unknown key, pass through
    end

    -- Handle Ctrl+key (no other modifiers except Shift for Ctrl+Shift+key)
    if flags.ctrl and not flags.cmd and not flags.alt then
        log.i("Detected Ctrl+" .. keyChar)

        -- Check if we should pass through to terminal apps
        if should_passthrough_ctrl() then
            log.i("→ Passing through Ctrl+" .. keyChar)
            return false  -- Pass through to app
        end

        -- Check if this key should be remapped
        if ctrl_to_cmd_set[keyChar] then
            -- Special handling for Ctrl+Shift+key
            if flags.shift then
                -- Ctrl+Shift+Z → Cmd+Shift+Z (redo)
                -- Ctrl+Shift+T → Cmd+Shift+T (reopen tab)
                if keyChar == "z" or keyChar == "t" then
                    log.i("→ Remapping Ctrl+Shift+" .. keyChar .. " → Cmd+Shift+" .. keyChar)
                    hs.eventtap.keyStroke({"cmd", "shift"}, keyChar)
                    return true  -- Consume the event
                end
            else
                -- Ctrl+key → Cmd+key
                log.i("→ Remapping Ctrl+" .. keyChar .. " → Cmd+" .. keyChar)
                hs.eventtap.keyStroke({"cmd"}, keyChar)
                return true  -- Consume the event
            end
        end
    end

    -- Handle Alt+Q → Cmd+Q (quit, accounting for global swap)
    -- After global Cmd↔Alt swap, physical Cmd appears as Alt to macOS
    if flags.alt and not flags.ctrl and not flags.cmd and not flags.shift then
        if keyChar == "q" then
            log.d("Remapping Alt+Q → Cmd+Q")
            hs.eventtap.keyStroke({"cmd"}, "q")
            return true  -- Consume the event
        end
    end

    return false  -- Pass through all other keys
end

-- ============================================================================
-- Module Control
-- ============================================================================

function PcShortcuts.start()
    if not PcShortcuts.config.enabled then return end

    if PcShortcuts.eventtap then
        log.w("PC shortcuts already started")
        return
    end

    log.i("Starting PC shortcuts module with eventtap")

    -- Create eventtap to intercept key events
    PcShortcuts.eventtap = hs.eventtap.new({hs.eventtap.event.types.keyDown}, handle_key_event)
    PcShortcuts.eventtap:start()

    log.i("PC shortcuts started - Ctrl keys will be remapped except in terminals")
end

function PcShortcuts.stop()
    log.i("Stopping PC shortcuts")

    if PcShortcuts.eventtap then
        PcShortcuts.eventtap:stop()
        PcShortcuts.eventtap = nil
    end

    log.i("PC shortcuts stopped")
end

-- ============================================================================
-- Auto-start
-- ============================================================================

if PcShortcuts.config.enabled then
    PcShortcuts.start()
end

log.i("PC shortcuts module loaded")

return PcShortcuts
