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
