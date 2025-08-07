return {
	"greggh/claude-code.nvim",
	dependencies = {
		"nvim-lua/plenary.nvim", -- Required for git operations
	},
	config = function()
		-- All keymaps are now managed in custom/keymaps.lua
		require("claude-code").setup({
			-- Terminal window settings
			window = {
				split_ratio = 0.3, -- How much screen real estate to give Claude (height/width)
				position = "botright", -- Where to put the window ("botright", "topleft", etc.)
				enter_insert = true, -- Jump right into typing mode
				hide_numbers = true, -- Clean up the UI a bit
			},

			-- Auto-reload when Claude updates your files
			refresh = {
				enable = true, -- This is like magic - Claude edits a file, it updates in Neovim!
				timer_interval = 1000, -- Check for changes every second
				show_notifications = true, -- "Psst, Claude just changed something!"
			},

			-- Git settings (very handy!)
			git = {
				use_git_root = false, -- Use Neovim's cwd instead of git root
			},
		})
	end,
}