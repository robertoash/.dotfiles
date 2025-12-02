-- Disable LSPs for qutebrowser config.py
vim.api.nvim_create_autocmd("BufReadPre", {
	pattern = {
		"*/.config/qutebrowser/config.py",
		"*/.config/qutebrowser/profiles/*/config/config.py",
	},
	callback = function()
		vim.diagnostic.enable(false, {
			bufnr = 0,
			filter = function(_)
				return true -- Disable all diagnostics for this buffer
			end,
		})
	end,
})
