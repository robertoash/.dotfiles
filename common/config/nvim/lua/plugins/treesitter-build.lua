-- Fallback script to compile tree-sitter parsers if nvim-treesitter.install() fails
local M = {}

function M.compile_missing_parsers()
	local parser_dir = vim.fn.stdpath("data") .. "/lazy/nvim-treesitter/parser"
	local cache_dir = vim.fn.expand("~/.cache/nvim")

	-- Create parser directory if missing
	vim.fn.mkdir(parser_dir, "p")

	-- List of parsers we need
	local parsers = {
		"bash",
		"c",
		"diff",
		"html",
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
	}

	local compiled = 0
	local failed = 0

	for _, parser in ipairs(parsers) do
		local parser_file = parser_dir .. "/" .. parser .. ".so"
		if vim.fn.filereadable(parser_file) == 0 then
			-- Parser missing, try to compile it
			local src_dir = cache_dir .. "/tree-sitter-" .. parser
			if vim.fn.isdirectory(src_dir .. "/src") == 1 then
				-- Compile parser
				local cmd = string.format(
					"gcc -shared -fPIC -O2 %s/src/*.c -I %s/src -o %s 2>&1",
					src_dir,
					src_dir,
					parser_file
				)
				local result = vim.fn.system(cmd)
				if vim.v.shell_error == 0 then
					compiled = compiled + 1
				else
					failed = failed + 1
					vim.notify(
						string.format("Failed to compile %s parser: %s", parser, result),
						vim.log.levels.ERROR
					)
				end
			end
		end
	end

	if compiled > 0 then
		vim.notify(string.format("Compiled %d missing parsers", compiled), vim.log.levels.INFO)
	end

	if failed > 0 then
		vim.notify(string.format("%d parsers failed to compile", failed), vim.log.levels.WARN)
	end
end

return M
