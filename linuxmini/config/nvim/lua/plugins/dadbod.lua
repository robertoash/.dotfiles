return {
	"tpope/vim-dadbod",
	dependencies = {
		"kristijanhusak/vim-dadbod-ui",
		"kristijanhusak/vim-dadbod-completion",
	},
	-- Keymaps are now managed in custom/keymaps.lua
	config = function()
		-- Note: vim-dadbod-completion typically integrates with nvim-cmp
		-- Since this config uses blink.cmp, you may need to manually configure
		-- completion for SQL files or use blink.cmp's buffer completion

		-- Set up dadbod-ui variables
		vim.g.db_ui_use_nerd_fonts = 1
		vim.g.db_ui_show_database_icon = 1
		vim.g.db_ui_force_echo_notifications = 1
		vim.g.db_ui_win_position = "left"
		vim.g.db_ui_winwidth = 40

		-- Auto-execute queries on save (optional)
		vim.g.db_ui_auto_execute_table_helpers = 1
	end,
}
