--=============================================================================
-- AUTOCOMMANDS
--=============================================================================
-- Force tabs to spaces after guess-indent
vim.api.nvim_create_autocmd("BufReadPost", {
	callback = function()
		-- If guess-indent chose tabs, override with your own taste
		if not vim.o.expandtab then
			vim.o.expandtab = true
			vim.o.shiftwidth = 4
			vim.o.tabstop = 4
		end
	end,
})

-- Highlight when yanking (copying) text
vim.api.nvim_create_autocmd("TextYankPost", {
	desc = "Highlight when yanking (copying) text",
	group = vim.api.nvim_create_augroup("kickstart-highlight-yank", { clear = true }),
	callback = function()
		vim.hl.on_yank()
	end,
})

vim.api.nvim_create_autocmd("BufReadPost", {
	callback = function(args)
		local file = vim.api.nvim_buf_get_name(args.buf)
		-- Exclude non-file buffers, like [No Name] or help
		if vim.fn.filereadable(file) == 1 then
			-- Call out to shell to add to fre
			vim.fn.jobstart({ "fre", "--add", file })
		end
	end,
})

-- Explicitly ensure JSON files have no conceallevel
vim.api.nvim_create_autocmd("FileType", {
	pattern = { "json", "jsonc" },
	callback = function()
		vim.opt_local.conceallevel = 0
		vim.opt_local.formatprg = "jq"
		vim.opt_local.wrap = false
	end,
	desc = "Configure JSON files with no concealment, jq formatter, and no wrapping",
})

-- Format JSON files on open
vim.api.nvim_create_autocmd("BufReadPost", {
	pattern = "*.json",
	callback = function()
		if vim.fn.executable("jq") == 1 then
			vim.cmd([[%!jq]])
		end
	end,
	desc = "Auto-format JSON files with jq on open",
})

-- Format JSON files on save
vim.api.nvim_create_autocmd("BufWritePre", {
	pattern = "*.json",
	callback = function()
		if vim.fn.executable("jq") == 1 then
			vim.cmd([[%!jq]])
		end
	end,
	desc = "Auto-format JSON files with jq on save",
})

-- Return the module
return {}
