local wezterm = require("wezterm")
local config = wezterm.config_builder()

-- ========================================
-- SHELL CONFIGURATION
-- ========================================

-- Always use fish shell as default
-- GUI apps on macOS don't inherit PATH, so use full path on macOS
if wezterm.target_triple:find("darwin") then
	local user = os.getenv("USER")
	config.default_prog = { "/etc/profiles/per-user/" .. user .. "/bin/fish" }
else
	config.default_prog = { "fish" }
end

-- ========================================
-- APPEARANCE & COLORS
-- ========================================

-- Tokyo Night Deep Color Scheme
config.colors = {
	-- Basic colors
	foreground = "#ffffff",
	background = "#010111",
	cursor_bg = "#7dcfff",
	cursor_fg = "#010111",
	cursor_border = "#7dcfff",
	selection_fg = "#ffffff",
	selection_bg = "#515c7e",

	-- Scrollbar
	scrollbar_thumb = "#363b54",

	-- Split borders
	split = "#363b54",

	-- ANSI colors
	ansi = {
		"#363b54", -- black (color0)
		"#f7768e", -- red (color1)
		"#41a6b5", -- green (color2)
		"#e6c100", -- yellow (color3)
		"#7aa2f7", -- blue (color4)
		"#bb9af7", -- magenta (color5)
		"#7dcfff", -- cyan (color6)
		"#b9bdcc", -- white (color7)
	},

	-- Bright ANSI colors
	brights = {
		"#454c6d", -- bright black (color8)
		"#ff5f8f", -- bright red (color9)
		"#00ffbb", -- bright green (color10)
		"#ffee00", -- bright yellow (color11)
		"#82aaff", -- bright blue (color12)
		"#d5a6ff", -- bright magenta (color13)
		"#8bffff", -- bright cyan (color14)
		"#d0d6e3", -- bright white (color15)
	},

	-- Tab bar colors
	tab_bar = {
		background = "#010111",
		active_tab = {
			bg_color = "#7aa2f7",
			fg_color = "#ffffff",
			intensity = "Bold",
		},
		inactive_tab = {
			bg_color = "#363b54",
			fg_color = "#b9bdcc",
		},
		inactive_tab_hover = {
			bg_color = "#454c6d",
			fg_color = "#ffffff",
		},
		new_tab = {
			bg_color = "#363b54",
			fg_color = "#b9bdcc",
		},
		new_tab_hover = {
			bg_color = "#454c6d",
			fg_color = "#ffffff",
		},
	},
}

-- Disable ligatures
config.harfbuzz_features = { "calt=0", "clig=0", "liga=0" }

-- Window appearance
config.window_background_opacity = 0.8

-- Window decorations: detect platform and desktop environment
local is_macos = wezterm.target_triple:find("darwin") ~= nil

-- Enable Wayland on Linux, disable on macOS
if is_macos then
	config.enable_wayland = false
else
	config.enable_wayland = true
end

-- Check if running Hyprland
local function is_hyprland()
	local desktop = os.getenv("XDG_CURRENT_DESKTOP") or ""
	local session = os.getenv("DESKTOP_SESSION") or ""
	return desktop:match("Hyprland") or session:match("hyprland")
end

-- Configure window decorations
if is_hyprland() then
	-- Hyprland: no decorations
	config.window_decorations = "NONE"
else
	-- macOS / other DEs: native decorations with window size
	config.initial_cols = 175
	config.initial_rows = 42
	config.window_decorations = "RESIZE"
end

-- ========================================
-- TABS CONFIGURATION
-- ========================================

config.enable_tab_bar = true
config.hide_tab_bar_if_only_one_tab = true
config.use_fancy_tab_bar = false

-- ========================================
-- FONT CONFIGURATION
-- ========================================

config.font = wezterm.font("GeistMono Nerd Font", { weight = "Regular" })
config.font_size = 14

-- ========================================
-- WINDOW & LAYOUT
-- ========================================

-- Window padding (similar to kitty's window_padding_width 20 20 15)
config.window_padding = {
	left = 20,
	right = 20,
	top = 20,
	bottom = 15,
}

-- Copy behavior (like kitty's copy_on_select)
config.selection_word_boundary = " \t\n{}[]()\"'`"

-- ========================================
-- TERMINAL BEHAVIOR
-- ========================================

-- Scrollback (like kitty's scrollback_lines 10000)
config.scrollback_lines = 10000

-- Mouse behavior (like kitty's mouse_hide_wait -1)
config.hide_mouse_cursor_when_typing = true

-- Cursor configuration (like kitty's cursor settings)
config.default_cursor_style = "SteadyBlock"

-- Audio (like kitty's enable_audio_bell no)
config.audible_bell = "Disabled"

-- Window behavior (like kitty's confirm_os_window_close 0)
config.window_close_confirmation = "NeverPrompt"

-- ========================================
-- HYPERLINKS CONFIGURATION
-- ========================================

-- Use the default hyperlink rules (recommended for troubleshooting)
config.hyperlink_rules = wezterm.default_hyperlink_rules()

-- Configure bypass for mouse reporting (needed for fish shell)
config.bypass_mouse_reporting_modifiers = "SHIFT"

-- ========================================
-- MOUSE BINDINGS
-- ========================================

-- Mouse bindings for clickable links
config.mouse_bindings = {
	-- Shift+click to open hyperlinks (works with fish shell mouse support)
	{
		event = { Up = { streak = 1, button = "Left" } },
		mods = "SHIFT",
		action = wezterm.action.OpenLinkAtMouseCursor,
	},
}

-- ========================================
-- KEYBOARD SHORTCUTS
-- ========================================

config.keys = {

	-- ----------------------------------------
	-- DISABLE DEFAULTS
	-- ----------------------------------------

	{
		key = "Enter",
		mods = "ALT",
		action = wezterm.action.DisableDefaultAssignment,
	},

	-- Claude Code integration
	{
		key = "Enter",
		mods = "SHIFT",
		action = wezterm.action.SendString("\x1b\r"),
	},

	-- ----------------------------------------
	-- UTILITY SHORTCUTS
	-- ----------------------------------------

	-- Quick open URLs (like kitty's hints)
	{
		key = "e",
		mods = "CTRL|SHIFT",
		action = wezterm.action.QuickSelect,
	},

	-- Copy mode (similar to kitty's line selection)
	{
		key = "x",
		mods = "CTRL|SHIFT",
		action = wezterm.action.ActivateCopyMode,
	},

	-- ----------------------------------------
	-- WORD NAVIGATION
	-- ----------------------------------------

	-- Navigate through words (like kitty's alt+left/right)
	{
		key = "LeftArrow",
		mods = "ALT",
		action = wezterm.action.SendString("\x1b[1;3D"),
	},
	{
		key = "RightArrow",
		mods = "ALT",
		action = wezterm.action.SendString("\x1b[1;3C"),
	},

	-- Custom word movement with Ctrl+h (backward) and Ctrl+l (forward)
	-- These send custom escape sequences that fish will handle
	{
		key = "h",
		mods = "CTRL",
		action = wezterm.action.SendString("\x1b[1;5H"), -- Custom sequence for backward word
	},
	{
		key = "l",
		mods = "CTRL",
		action = wezterm.action.SendString("\x1b[1;5L"), -- Custom sequence for forward word
	},

	-- Space-only word movement with Ctrl+Shift+h and Ctrl+Shift+l
	-- These ignore slashes and only treat spaces as delimiters
	{
		key = "h",
		mods = "CTRL|SHIFT",
		action = wezterm.action.SendString("\x1b[1;6H"), -- Custom sequence for backward word (space-only)
	},
	{
		key = "l",
		mods = "CTRL|SHIFT",
		action = wezterm.action.SendString("\x1b[1;6L"), -- Custom sequence for forward word (space-only)
	},

	-- Ctrl+Tab to accept autosuggestion with slashes (unique sequence)
	{
		key = "Tab",
		mods = "CTRL",
		action = wezterm.action.SendString("\x1b[27;5;9~"), -- Proper Ctrl+Tab sequence
	},

	-- ----------------------------------------
	-- WORD DELETION
	-- ----------------------------------------

	-- Word deletion keybinds
	{
		key = "Delete",
		mods = "CTRL",
		action = wezterm.action.SendString("\x1b[3;5~"), -- Delete forward word
	},
	{
		key = "Backspace",
		mods = "CTRL",
		action = wezterm.action.SendString("\x1b[127;5u"), -- Delete backward word
	},

	-- Space-only word deletion keybinds
	{
		key = "Delete",
		mods = "CTRL|SHIFT",
		action = wezterm.action.SendString("\x1b[3;6~"), -- Delete forward word (space-only)
	},
	{
		key = "Backspace",
		mods = "CTRL|SHIFT",
		action = wezterm.action.SendString("\x1b[127;6u"), -- Delete backward word (space-only)
	},
}

-- ========================================
-- COPY MODE KEY TABLE
-- ========================================

config.key_tables = {
	copy_mode = {
		-- Move 10 lines up with Ctrl+UpArrow
		{
			key = "UpArrow",
			mods = "CTRL",
			action = wezterm.action.CopyMode({ MoveByPage = -0.25 }),
		},
		-- Move 10 lines down with Ctrl+DownArrow
		{
			key = "DownArrow",
			mods = "CTRL",
			action = wezterm.action.CopyMode({ MoveByPage = 0.25 }),
		},
		-- Exit copy mode with Escape
		{
			key = "Escape",
			mods = "NONE",
			action = wezterm.action.CopyMode("Close"),
		},
		-- Copy selection and exit
		{
			key = "Enter",
			mods = "NONE",
			action = wezterm.action.Multiple({
				wezterm.action.CopyTo("ClipboardAndPrimarySelection"),
				wezterm.action.CopyMode("Close"),
			}),
		},
	},
}

-- ========================================
-- RETURN CONFIG
-- ========================================

return config
