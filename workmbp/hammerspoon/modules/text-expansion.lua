-- ============================================================================
-- Text Expansion Module
-- ============================================================================
-- Text expansion/replacement functionality
-- Replaces: espanso / macOS text replacements
-- ============================================================================

TextExpansion = TextExpansion or {}

local log = hs.logger.new('text-expansion', 'info')

-- State
TextExpansion.watcher = nil
TextExpansion.enabled = false
TextExpansion.current_word = ""
TextExpansion.max_trigger_length = 20  -- Maximum length of expansion trigger

-- ============================================================================
-- Text Expansion Implementation
-- ============================================================================

-- Handle key events
local function on_key_event(event)
    if not Config.preferences.text_expansion_enabled then
        return false
    end

    local char = event:getCharacters()
    local keycode = event:getKeyCode()
    local flags = event:getFlags()

    -- Ignore modifier-only events
    if not char or char == "" then
        return false
    end

    -- Reset buffer on space, enter, or modifiers (except shift)
    if char == " " or keycode == 36 or flags.cmd or flags.ctrl or flags.alt then
        TextExpansion.current_word = ""
        return false
    end

    -- Handle backspace
    if keycode == 51 then  -- delete/backspace
        if #TextExpansion.current_word > 0 then
            TextExpansion.current_word = TextExpansion.current_word:sub(1, -2)
        end
        return false
    end

    -- Append character to current word
    TextExpansion.current_word = TextExpansion.current_word .. char

    -- Limit buffer size
    if #TextExpansion.current_word > TextExpansion.max_trigger_length then
        TextExpansion.current_word = TextExpansion.current_word:sub(-TextExpansion.max_trigger_length)
    end

    -- Check for expansion match
    for trigger, expansion in pairs(Constants.text_expansions) do
        if Helpers.ends_with(TextExpansion.current_word, trigger) then
            log.f("Expanding: %s -> %s", trigger, expansion)

            -- Delete the trigger text
            Helpers.delete_chars(#trigger)

            -- Type the expansion
            Helpers.type_string(expansion)

            -- Reset buffer
            TextExpansion.current_word = ""

            return false
        end
    end

    return false
end

-- ============================================================================
-- Module Control
-- ============================================================================

-- Start text expansion
function TextExpansion.start()
    if TextExpansion.enabled then
        log.w("Text expansion already enabled")
        return
    end

    log.i("Starting text expansion")

    -- Create keyboard event watcher
    TextExpansion.watcher = hs.eventtap.new(
        {hs.eventtap.event.types.keyDown},
        on_key_event
    )

    TextExpansion.watcher:start()
    TextExpansion.enabled = true

    log.i("Text expansion started")

    -- Log loaded expansions
    local count = Helpers.table_size(Constants.text_expansions)
    log.f("Loaded %d text expansions", count)
end

-- Stop text expansion
function TextExpansion.stop()
    if not TextExpansion.enabled then
        log.w("Text expansion already disabled")
        return
    end

    log.i("Stopping text expansion")

    if TextExpansion.watcher then
        TextExpansion.watcher:stop()
        TextExpansion.watcher = nil
    end

    TextExpansion.enabled = false
    TextExpansion.current_word = ""

    log.i("Text expansion stopped")
end

-- Toggle text expansion
function TextExpansion.toggle()
    if TextExpansion.enabled then
        TextExpansion.stop()
        Helpers.alert("Text expansion disabled")
    else
        TextExpansion.start()
        Helpers.alert("Text expansion enabled")
    end
end

-- ============================================================================
-- Auto-start
-- ============================================================================

if Config.preferences.text_expansion_enabled then
    TextExpansion.start()
end

log.i("Text expansion module loaded")

return TextExpansion
