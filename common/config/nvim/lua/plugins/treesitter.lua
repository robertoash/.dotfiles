return {
	{
		"nvim-treesitter/nvim-treesitter",
		branch = "main",
		build = function()
			-- Install parsers after plugin is built/updated
			local ts = require("nvim-treesitter")
			ts.install({
				"bash",
				"c",
				"diff",
				"html",
				"jinja",
				"lua",
				"luadoc",
				"markdown",
				"markdown_inline",
				"python",
				"query",
				"regex",
				"sql",
				"vim",
				"vimdoc",
				"yaml",
			})
		end,
		config = function()
			-- Enable highlighting via autocommand
			vim.api.nvim_create_autocmd("FileType", {
				pattern = "*",
				callback = function()
					pcall(vim.treesitter.start)
				end,
			})

			-- Enable indentation for supported languages
			vim.api.nvim_create_autocmd("FileType", {
				pattern = { "bash", "c", "html", "lua", "python", "sql", "vim", "yaml" },
				callback = function()
					vim.bo.indentexpr = "v:lua.require'nvim-treesitter.indent'.get_indent(v:lnum)"
				end,
			})
		end,
	},
	{
		"nvim-treesitter/nvim-treesitter-context",
		config = function()
			require("treesitter-context").setup({
				enable = true,
				max_lines = 0,
				trim_scope = "outer",
				mode = "cursor",
				separator = "─",
			})
		end,
	},
}
