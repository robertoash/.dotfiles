return {
	"rickhowe/wrapwidth",
	ft = { "markdown", "text" },
	config = function()
		-- Auto-enable wrapwidth for markdown and text files
		vim.api.nvim_create_autocmd("FileType", {
			pattern = { "markdown", "text" },
			callback = function()
				-- Set wrapwidth to 88 columns for the entire buffer
				vim.cmd("Wrapwidth 100")
			end,
		})
	end,
}
