return {
	{
		"nvim-treesitter/nvim-treesitter",
		branch = "main",
		build = function()
			-- Set parser directory before installing
			local install = require("nvim-treesitter.install")
			install.parser_dir = vim.fn.stdpath("data") .. "/lazy/nvim-treesitter/parser"

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
			-- Set parser directory for runtime
			local install = require("nvim-treesitter.install")
			install.parser_dir = vim.fn.stdpath("data") .. "/lazy/nvim-treesitter/parser"

			-- Prepend parser directory to runtimepath so nvim-treesitter parsers override system ones
			vim.opt.runtimepath:prepend(vim.fn.stdpath("data") .. "/lazy/nvim-treesitter")

			-- Auto-install missing parsers on first run
			local parser_dir = vim.fn.stdpath("data") .. "/lazy/nvim-treesitter/parser"
			vim.fn.mkdir(parser_dir, "p")
			local parsers_exist = #vim.fn.glob(parser_dir .. "/*.so", false, true) > 0

			if not parsers_exist then
				-- Schedule async to avoid blocking startup
				vim.schedule(function()
					vim.notify("Installing tree-sitter parsers...", vim.log.levels.INFO)
					require("nvim-treesitter").install({
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
				end)
			end

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
