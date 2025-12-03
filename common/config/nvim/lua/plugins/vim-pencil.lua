return {
	"preservim/vim-pencil",
	ft = { "markdown", "text" },
	config = function()
		-- Configure vim-pencil defaults
		vim.g["pencil#wrapModeDefault"] = "soft" -- Default to soft line wrap
		vim.g["pencil#textwidth"] = 88 -- Set textwidth for hard wrap mode
		vim.g["pencil#joinspaces"] = 0 -- Single space after punctuation
		vim.g["pencil#cursorwrap"] = 1 -- Allow cursor to wrap at line boundaries
		vim.g["pencil#conceallevel"] = 1 -- Set conceallevel for markdown

		-- Auto-initialize vim-pencil for markdown and text files
		vim.api.nvim_create_autocmd("FileType", {
			pattern = { "markdown", "text" },
			callback = function()
				vim.fn["pencil#init"]({ wrap = "soft", textwidth = 88 })
				-- Disable auto-wrap while typing (remove 't' from formatoptions)
				vim.opt_local.formatoptions = "jcroql"
			end,
		})
	end,
}
