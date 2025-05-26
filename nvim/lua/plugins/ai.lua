return {
	{
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
					use_git_root = true, -- Start Claude in the project root
				},
			})
		end,
	},

	{
		"yetone/avante.nvim",
		event = "VeryLazy",
		version = false, -- Never set this value to "*"! Never!
		lazy = false,
		-- if you want to build from source then do `make BUILD_FROM_SOURCE=true`
		build = "make",
		-- build = "powershell -ExecutionPolicy Bypass -File Build.ps1 -BuildFromSource false" -- for windows
		opts = {
			-- add any opts here
			-- for example
			provider = "claude",
			openai = {
				endpoint = "https://api.openai.com/v1",
				model = "gpt-4o", -- your desired model (or use gpt-4o, etc.)
				timeout = 30000, -- Timeout in milliseconds, increase this for reasoning models
				temperature = 0,
				max_completion_tokens = 8192, -- Increase this to include reasoning tokens (for reasoning models)
				--reasoning_effort = "medium", -- low|medium|high, only used for reasoning models
			},
			claude = {
				endpoint = "https://api.anthropic.com",
				model = "claude-3-5-sonnet-20241022", -- Or your preferred Claude model
				temperature = 0,
				max_tokens = 4096,
			},
			auto_suggestions_provider = "claude",
		},
		dependencies = {
			"nvim-treesitter/nvim-treesitter",
			"stevearc/dressing.nvim",
			"nvim-lua/plenary.nvim",
			"MunifTanjim/nui.nvim",
			--- The below dependencies are optional,
			"echasnovski/mini.pick", -- for file_selector provider mini.pick
			"nvim-telescope/telescope.nvim", -- for file_selector provider telescope
			"hrsh7th/nvim-cmp", -- autocompletion for avante commands and mentions
			"ibhagwan/fzf-lua", -- for file_selector provider fzf
			"nvim-tree/nvim-web-devicons", -- or echasnovski/mini.icons
			"zbirenbaum/copilot.lua", -- for providers='copilot'
			{
				-- support for image pasting
				"HakonHarnes/img-clip.nvim",
				event = "VeryLazy",
				opts = {
					-- recommended settings
					default = {
						embed_image_as_base64 = false,
						prompt_for_file_name = false,
						drag_and_drop = {
							insert_mode = true,
						},
						-- required for Windows users
						use_absolute_path = true,
					},
				},
			},
			{
				-- Make sure to set this up properly if you have lazy=true
				"MeanderingProgrammer/render-markdown.nvim",
				opts = {
					file_types = { "Avante" },
				},
				ft = { "Avante" },
			},
			--
		},
	},
}
