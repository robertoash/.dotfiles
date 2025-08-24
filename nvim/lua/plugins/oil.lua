return {
	"stevearc/oil.nvim",
	---@module 'oil'
	---@type oil.SetupOpts
	config = function()
		-- Get keymaps from the keymaps module
		local keymaps = require("custom.keymaps").get_oil_keymaps()
		
		require("oil").setup({
			keymaps = keymaps,
		})
	end,
	-- Optional dependencies
	dependencies = { { "echasnovski/mini.icons", opts = {} } },
	-- dependencies = { "nvim-tree/nvim-web-devicons" }, -- use if you prefer nvim-web-devicons
}