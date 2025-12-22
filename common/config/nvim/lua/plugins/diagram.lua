return {
	"3rd/diagram.nvim",
	dependencies = {
		"3rd/image.nvim",
	},
	config = function()
		require("diagram").setup({
			integrations = {
				require("diagram.integrations.markdown"),
			},
			events = {
				render_buffer = { "InsertLeave", "BufWinEnter", "TextChanged" },
				clear_buffer = { "BufLeave" },
			},
			renderer_options = {
				mermaid = {
					background = nil, -- nil | "transparent" | "white" | "#hex"
					theme = nil, -- nil | "default" | "dark" | "forest" | "neutral"
					scale = 1, -- nil | 1 (default) | 2  | 3 | ...
				},
			},
		})
	end,
}