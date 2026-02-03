return {
	-- sqlit integration - Terminal UI for SQL databases in a floating window
	{
		name = "sqlit",
		dir = vim.fn.stdpath("config"),
		config = function()
			local function open_sqlit_float(args)
				args = args or ""
				local width = math.floor(vim.o.columns * 0.9)
				local height = math.floor(vim.o.lines * 0.9)
				local row = math.floor((vim.o.lines - height) / 2)
				local col = math.floor((vim.o.columns - width) / 2)

				local buf = vim.api.nvim_create_buf(false, true)
				local win = vim.api.nvim_open_win(buf, true, {
					relative = "editor",
					width = width,
					height = height,
					row = row,
					col = col,
					style = "minimal",
					border = "rounded",
				})

				vim.fn.termopen("uv run sqlit " .. args, {
					on_exit = function()
						vim.api.nvim_buf_delete(buf, { force = true })
					end,
				})

				vim.cmd("startinsert")

				-- Close with q in normal mode
				vim.keymap.set("n", "q", function()
					vim.api.nvim_win_close(win, true)
				end, { buffer = buf })
			end

			vim.api.nvim_create_user_command("Sqlit", function(opts)
				open_sqlit_float(opts.args)
			end, {
				nargs = "*",
				desc = "Open sqlit TUI in a floating window",
			})
		end,
	},
}
