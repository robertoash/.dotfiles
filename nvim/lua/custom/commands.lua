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

--=============================================================================
-- CUSTOM COMMANDS
--=============================================================================
-- :W - write with mkdir -p
vim.api.nvim_create_user_command("W", function()
	local file = vim.api.nvim_buf_get_name(0)
	local dir = vim.fn.fnamemodify(file, ":p:h")
	if vim.fn.isdirectory(dir) == 0 then
		vim.fn.mkdir(dir, "p")
	end
	vim.cmd("write")
end, {})

-- :WQ - write and quit with mkdir -p
vim.api.nvim_create_user_command("WQ", function()
	local file = vim.api.nvim_buf_get_name(0)
	local dir = vim.fn.fnamemodify(file, ":p:h")
	if vim.fn.isdirectory(dir) == 0 then
		vim.fn.mkdir(dir, "p")
	end
	vim.cmd("wq")
end, {})

-- Return the module
return {}

