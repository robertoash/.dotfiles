return {

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
