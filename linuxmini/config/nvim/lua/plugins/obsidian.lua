return {
	"epwalsh/obsidian.nvim",
	version = "*", -- recommended, use latest release instead of latest commit
	lazy = true,
	-- Load specifically for your Obsidian vault
	event = {
		"BufReadPre " .. vim.fn.expand("~") .. "/obsidian/vault/*.md",
		"BufNewFile " .. vim.fn.expand("~") .. "/obsidian/vault/*.md",
		"BufReadPre " .. vim.fn.expand("~") .. "/obsidian/vault/**/*.md",
		"BufNewFile " .. vim.fn.expand("~") .. "/obsidian/vault/**/*.md",
	},
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
