return {
	"stevearc/oil.nvim",
	---@module 'oil'
	---@type oil.SetupOpts
	opts = {
		keymaps = {
			-- More intuitive navigation up
			["H"] = "actions.parent",
			["<BS>"] = "actions.parent",
			-- Keep the default - as well
			["-"] = "actions.parent",
		},
	},
	-- Optional dependencies
	dependencies = { { "echasnovski/mini.icons", opts = {} } },
	-- dependencies = { "nvim-tree/nvim-web-devicons" }, -- use if you prefer nvim-web-devicons
}