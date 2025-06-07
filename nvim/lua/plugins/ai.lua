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
		version = false,
		lazy = false,
		build = "make",
		opts = {
			provider = "claude",
			auto_suggestions_provider = "claude",

			providers = {
				claude = {
					endpoint = "https://api.anthropic.com",
					model = "claude-3-5-sonnet-20241022",
					extra_request_body = {
						temperature = 0,
						max_tokens = 4096,
					},

					window = {
						split_ratio = 0.3,
						position = "botright",
						enter_insert = true,
						hide_numbers = true,
					},
					refresh = {
						enable = true,
						timer_interval = 1000,
						show_notifications = true,
					},
					git = {
						use_git_root = true,
					},
				},
			},
		},

		dependencies = {
			"nvim-treesitter/nvim-treesitter",
			"stevearc/dressing.nvim",
			"nvim-lua/plenary.nvim",
			"MunifTanjim/nui.nvim",
			"echasnovski/mini.pick",
			"nvim-telescope/telescope.nvim",
			"hrsh7th/nvim-cmp",
			"ibhagwan/fzf-lua",
			"nvim-tree/nvim-web-devicons",
			"zbirenbaum/copilot.lua",
			{
				"HakonHarnes/img-clip.nvim",
				event = "VeryLazy",
				opts = {
					default = {
						embed_image_as_base64 = false,
						prompt_for_file_name = false,
						drag_and_drop = {
							insert_mode = true,
						},
						use_absolute_path = true,
					},
				},
			},
			{
				"MeanderingProgrammer/render-markdown.nvim",
				ft = { "Avante" },
				opts = {
					file_types = { "Avante" },
				},
			},
		},
	},
}
