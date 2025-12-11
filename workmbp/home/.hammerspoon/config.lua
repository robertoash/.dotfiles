-- ============================================================================
-- Hammerspoon Configuration
-- ============================================================================
-- Centralized configuration for all Hammerspoon modules
-- ============================================================================

Config = Config or {}

-- ============================================================================
-- Window Layout Settings
-- ============================================================================

Config.layout = {
	-- Screen padding (space between screen edges and windows)
	padding = {
		top = 50, -- Space for sketchybar on external monitors (4px gap above + 35px bar + 8px gap below)
		bottom = 12,
		left = 12,
		right = 12,
	},

	-- Builtin display top gap (for untiled mode gap enforcement)
	-- Smaller value for Retina displays due to HiDPI scaling
	builtin_top_gap = 25, -- Reserved space at top of builtin display

	-- Window margins (gaps between windows)
	-- Set to 12px to account for border overlap in worst case:
	-- - Focused border (4px): 2px extends outside
	-- - Unfocused border (2px): 1px extends outside
	-- - Total overlap: 3px, leaving 9px visual gap (slightly more than 8px for safety)
	margin = 10,

	-- Master factor default (master window size ratio)
	default_mfact = 0.65, -- 65% of screen for master window

	-- Master factor adjustment step (for increase/decrease keybinds)
	mfact_step = 0.05, -- 5% per step

	-- Master factor limits
	mfact_min = 0.2, -- 20% minimum
	mfact_max = 0.8, -- 80% maximum
}

-- ============================================================================
-- Window Border Settings
-- ============================================================================

Config.borders = {
	-- Border width in pixels
	width_focused = 4,
	width_unfocused = 2, -- Half width for inactive windows

	-- Corner radius in pixels (macOS windows vary, this is a compromise)
	radius = 25,

	-- Regular window border colors
	focused = {
		red = 0xe6 / 255, -- #e6c100 (golden yellow)
		green = 0xc1 / 255,
		blue = 0x00 / 255,
		alpha = 1.0,
	},

	unfocused = {
		red = 0.5, -- Grey
		green = 0.5,
		blue = 0.5,
		alpha = 1.0, -- Fully opaque to prevent color artifacts
	},

	-- Pinned window border colors (special color to indicate pinned status)
	pinned_focused = {
		red = 0xff / 255, -- #ff5f8f (color9 - bright pink)
		green = 0x5f / 255,
		blue = 0x8f / 255,
		alpha = 1.0,
	},

	pinned_unfocused = {
		red = 0xf7 / 255, -- #f7768e (color1 - pink)
		green = 0x76 / 255,
		blue = 0x8e / 255,
		alpha = 1.0,
	},
}

-- ============================================================================
-- Window Management Rules
-- ============================================================================

Config.window_rules = {
	-- Whether new windows go to master or stack
	new_windows_to_main = false,

	-- Tile ALL windows (no floating based on size)
	float_small_windows = false,

	-- Apps that should never be tiled (only system dialogs that can't tile properly)
	floating_apps = {
		"System Preferences",
		"System Settings",
		"Calculator",
		"Archive Utility",
		"Hammerspoon",
	},
}

return Config
