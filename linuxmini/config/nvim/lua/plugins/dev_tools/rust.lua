return {
	{
		"simrat39/rust-tools.nvim",
		dependencies = { "neovim/nvim-lspconfig" },
		config = function()
			require("rust-tools").setup({
				tools = {
					executor = require("rust-tools/executors").termopen,
					autoSetHints = true,
					hover_with_actions = true,
					inlay_hints = {
						auto = true,
						only_current_line = false,
						show_parameter_hints = true,
						parameter_hints_prefix = "<- ",
						other_hints_prefix = "=> ",
						max_len_align = false,
						max_len_align_padding = 1,
						right_align = false,
						right_align_padding = 7,
						highlight = "Comment",
					},
					hover_actions = {
						border = {
							{ "╭", "FloatBorder" },
							{ "─", "FloatBorder" },
							{ "╮", "FloatBorder" },
							{ "│", "FloatBorder" },
							{ "╯", "FloatBorder" },
							{ "─", "FloatBorder" },
							{ "╰", "FloatBorder" },
							{ "│", "FloatBorder" },
						},
						auto_focus = true,
					},
				},
				server = {
					settings = {
						["rust-analyzer"] = {
							checkOnSave = {
								command = "clippy",
								extraArgs = { "--no-deps" },
							},
							procMacro = {
								enable = true,
							},
							cargo = {
								features = "all",
							},
							inlayHints = {
								enable = true,
							},
						},
					},
				},
			})
		end,
	},
}