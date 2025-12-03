return {
	"epwalsh/obsidian.nvim",
	version = "*", -- recommended, use latest release instead of latest commit
	lazy = true,
	-- Load specifically for your Obsidian vault
	event = {
		"BufReadPre " .. vim.fn.expand("~") .. "/obsidian/vault/*.md",
		"BufNewFile " .. vim.fn.expand("~") .. "/obsidian/vault/*.md",
	},
	-- Also check if file is within vault subdirectories
	cond = function()
		local bufpath = vim.api.nvim_buf_get_name(0)
		local vault_path = vim.fn.expand("~") .. "/obsidian/vault/"
		return bufpath:match("%.md$") and bufpath:find(vault_path, 1, true) ~= nil
	end,
	dependencies = {
		-- Required.
		"nvim-lua/plenary.nvim",

		-- see below for full list of optional dependencies 👇
	},
	opts = {
		workspaces = {
			{
				name = "rash",
				path = "~/obsidian/vault/",
			},
		},
		-- Disable obsidian UI to prevent conflict with render-markdown
		ui = {
			enable = false,
		},
	},
}
