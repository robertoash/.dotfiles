return {
	'mfussenegger/nvim-lint',
	config = function()
		require('lint').linters_by_ft = {
			sql = { 'sqlfluff' }
		}

		-- Configure sqlfluff for Snowflake
		require('lint').linters.sqlfluff.args = {
			'lint',
			'--format=json',
			'--dialect=snowflake',
		}

		-- Auto-lint on save and buffer enter
		vim.api.nvim_create_autocmd({ "BufWritePost", "BufEnter" }, {
			callback = function()
				require("lint").try_lint()
			end,
		})
	end,
}
