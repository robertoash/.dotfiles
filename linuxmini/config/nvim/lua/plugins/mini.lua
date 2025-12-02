return {
	"echasnovski/mini.nvim",
	version = false, -- wait till new 0.7.0 release to put it back on semver
	config = function()
		-- Better Around/Inside textobjects
		require("mini.ai").setup({ n_lines = 500 })

		-- Add/delete/replace surroundings (brackets, quotes, etc.)
		-- Keymaps are managed in custom/keymaps.lua
		require("mini.surround").setup()

		-- Split and join arguments, array elements, object properties, etc.
		-- Keymaps are managed in custom/keymaps.lua
		require("mini.splitjoin").setup({
			mappings = {
				toggle = "", -- Disable default toggle mapping
			},
		})
	end,
}