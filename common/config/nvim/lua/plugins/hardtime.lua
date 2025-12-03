return {
	"m4xshen/hardtime.nvim",
	lazy = false,
	dependencies = {
		"MunifTanjim/nui.nvim",
	},
	opts = {
		-- Allow some flexibility for browsing/exploring
		max_time = 2000, -- Allow holding keys for 2 seconds (default is 1000ms)
		max_count = 6, -- Allow 6 repeated keys instead of default 3
		-- Disable in certain filetypes where you browse more
		disabled_filetypes = { "qf", "netrw", "NvimTree", "lazy", "mason", "oil" },
		-- Add a keybind to toggle hardtime on/off
		hint = true, -- Show hints for better alternatives
		disabled_keys = {
			["<Up>"] = false, -- Allow <Up> key
			["<Down>"] = false, -- Allow <Up> key
			["<Left>"] = false, -- Allow <Up> key
			["<Right>"] = false, -- Allow <Up> key
		},
	},
}
