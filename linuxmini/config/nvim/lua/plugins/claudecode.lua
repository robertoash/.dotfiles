return {
	"coder/claudecode.nvim",
	dependencies = { "folke/snacks.nvim" },
	config = function()
		require("claudecode").setup({
			diff_opts = {
				layout = "vertical",
				open_in_new_tab = false,
				hide_terminal_in_new_tab = false,
				on_new_file_reject = "keep_empty",
				auto_close_on_accept = true,
				vertical_split = true,
				open_in_current_tab = true,
				keep_terminal_focus = true,
			},
			terminal = {
				auto_close = true,
				split_side = "right",
				split_width_percentage = 0.30,
				provider = "snacks",
			},
			track_selection = true,
			visual_demotion_delay_ms = 50,
		})

		-- Optional: Enable autoread to automatically reload changed files
		vim.opt.autoread = true

		-- Optional: Add autocmd to check for file changes when entering buffer
		vim.api.nvim_create_autocmd({ "FocusGained", "BufEnter", "CursorHold" }, {
			pattern = "*",
			command = "checktime",
		})

		-- Auto-reload buffer after accepting diff changes
		-- This detects when diff windows close and briefly focuses the original buffer to trigger reload
		local original_buf = nil
		vim.api.nvim_create_autocmd("WinEnter", {
			pattern = "*",
			callback = function()
				local ft = vim.bo.filetype
				if ft == "diff" or vim.wo.diff then
					-- Store the original buffer when entering diff
					original_buf = vim.fn.bufwinid(vim.fn.bufnr("#"))
				end
			end,
		})

		vim.api.nvim_create_autocmd("BufWritePost", {
			pattern = "*",
			callback = function()
				if vim.wo.diff and original_buf and original_buf ~= -1 then
					-- After saving in diff (accepting changes), briefly focus original buffer
					vim.defer_fn(function()
						-- Focus the original buffer to trigger checktime
						vim.api.nvim_set_current_win(original_buf)
						vim.cmd("checktime")
						-- Return to Claude terminal
						vim.defer_fn(function()
							vim.cmd("wincmd p") -- Return to previous window (terminal)
						end, 50)
					end, 100)
				end
			end,
		})
	end,
}
