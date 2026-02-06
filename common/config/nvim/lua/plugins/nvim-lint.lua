return {
	'mfussenegger/nvim-lint',
	config = function()
		local linters_by_ft = {}
		if vim.fn.hostname():match("workmbp") then
			linters_by_ft.sql = { "sqlfluff" }
			require("lint").linters.sqlfluff.args = {
				"lint",
				"--format=json",
				"--dialect=snowflake",
			}
		end
		require("lint").linters_by_ft = linters_by_ft

		-- Auto-lint on save and buffer enter
		vim.api.nvim_create_autocmd({ "BufWritePost", "BufEnter" }, {
			callback = function()
				require("lint").try_lint()
			end,
		})
	end,
}
