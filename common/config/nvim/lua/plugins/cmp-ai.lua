return {
	"tzachar/cmp-ai",
	dependencies = {
		"nvim-lua/plenary.nvim",
		"saghen/blink.compat",
	},
	config = function()
		local cmp_ai = require("cmp_ai.config")

		cmp_ai:setup({
			max_lines = 100,
			provider = "Anthropic",
			provider_options = {
				model = "claude-3-haiku-20240307",
			},
			notify = true,
			notify_callback = function(msg)
				vim.notify(msg, vim.log.levels.INFO)
			end,
			run_on_every_keystroke = false,
			ignored_file_types = {
				-- default is not to ignore
				-- uncomment to ignore in lua:
				-- lua = true
			},
		})
	end,
}
