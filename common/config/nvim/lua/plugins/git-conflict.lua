return {
	"tronikelis/conflict-marker.nvim",
	config = function()
		require("conflict-marker").setup({
			highlights = {
				current = "DiffText",
				incoming = "DiffAdd",
			},
			on_attach = function(bufnr)
				-- Trigger User event for keymaps.lua to attach buffer-local keymaps
				vim.api.nvim_exec_autocmds("User", { pattern = "ConflictMarkerSetup" })
			end,
		})
	end,
}
