return {
	"PedramNavid/dbtpal",
	dependencies = {
		"nvim-lua/plenary.nvim",
		"nvim-telescope/telescope.nvim",
	},
	ft = {
		"sql",
		"md",
		"yaml",
	},
	-- Keymaps are now managed in custom/keymaps.lua
	config = function()
		require("dbtpal").setup({
			path_to_dbt = "dbtf-clean", -- Use wrapper to filter dbtf output for dbtpal compatibility
			path_to_dbt_project = "",
			path_to_dbt_profiles_dir = vim.fn.expand("~/.dbt"),
			include_profiles_dir = false,
			include_project_dir = false,
			include_log_level = false,
			extended_path_search = true,
			protect_compiled_files = true,
			pre_cmd_args = {},
			post_cmd_args = {},
		})

		require("telescope").load_extension("dbtpal")
	end,
}
