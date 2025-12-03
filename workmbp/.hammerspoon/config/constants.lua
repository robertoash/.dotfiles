-- ============================================================================
-- Constants
-- ============================================================================
-- Shared constants used across modules
-- ============================================================================

Constants = Constants or {}

-- ============================================================================
-- Modifier Keys
-- ============================================================================
-- Hammerspoon modifier key mappings
-- cmd = Command, alt = Option, ctrl = Control, shift = Shift

Constants.mods = {
    cmd = {"cmd"},
    alt = {"alt"},
    ctrl = {"ctrl"},
    shift = {"shift"},

    -- Hyper key (Cmd+Ctrl+Option+Shift)
    hyper = {"cmd", "ctrl", "alt", "shift"},

    -- Common combinations
    cmd_ctrl = {"cmd", "ctrl"},
    cmd_alt = {"cmd", "alt"},
    cmd_shift = {"cmd", "shift"},
    ctrl_alt = {"ctrl", "alt"},
    ctrl_shift = {"ctrl", "shift"},
    alt_shift = {"alt", "shift"},

    -- Three-key combinations
    cmd_ctrl_alt = {"cmd", "ctrl", "alt"},
    cmd_ctrl_shift = {"cmd", "ctrl", "shift"},
    cmd_alt_shift = {"cmd", "alt", "shift"},
    ctrl_alt_shift = {"ctrl", "alt", "shift"},
}

-- LeftRightHotkey-specific modifiers (for use with LeftRightHotkey Spoon)
-- These use LOWERCASE syntax: "lalt", "ralt", "lcmd", etc.
-- ALL modifiers must be left/right variants when using LeftRightHotkey
Constants.leftRightMods = {
    lalt = {"lalt"},         -- Left Alt only (doesn't interfere with AltGr)
    ralt = {"ralt"},
    lcmd = {"lcmd"},
    rcmd = {"rcmd"},

    -- Common combinations with left modifiers
    lcmd_lalt = {"lcmd", "lalt"},  -- Left Cmd + Left Alt only
    lalt_lctrl = {"lalt", "lctrl"},  -- Left Alt + Left Ctrl
    lalt_lctrl_lshift = {"lalt", "lctrl", "lshift"},  -- Left Alt + Left Ctrl + Left Shift
}

-- ============================================================================
-- Application Paths
-- ============================================================================

Constants.apps = {
    wezterm = "/Applications/WezTerm.app",
    -- Add more apps as needed
}

-- ============================================================================
-- Text Expansion
-- ============================================================================
-- Text replacement mappings (from macOS text replacements)

Constants.text_expansions = {
    -- Email addresses
    [":email"] = "j.roberto.ash@gmail.com",
    [":work"] = "roberto.ash@readly.com",

    -- Addresses
    [":fv16"] = "Fornåsavägen 16",
    [":gv13"] = "Grundsjövägen 13",

    -- Contact
    [":phone"] = "+46764152336",

    -- Demo
    [":espanso"] = "Hi there!",
}
