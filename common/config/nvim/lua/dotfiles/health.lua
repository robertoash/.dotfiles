-- Custom health check for dotfiles Neovim setup
local M = {}

-- Health check function
M.check = function()
	local health = vim.health or require("health")
	local start = health.start or health.report_start
	local ok = health.ok or health.report_ok
	local warn = health.warn or health.report_warn
	local error = health.error or health.report_error
	local info = health.info or health.report_info

	start("Dotfiles Dependencies")

	-- Check for required build tools
	local required_tools = {
		{ name = "gcc", desc = "Required for tree-sitter parser compilation" },
		{ name = "git", desc = "Required for plugin management" },
		{ name = "unzip", desc = "Required for Mason LSP installations" },
		{ name = "tar", desc = "Required for Mason package extraction" },
		{ name = "gzip", desc = "Required for Mason package extraction" },
		{ name = "curl", desc = "Required for downloading plugins/tools" },
	}

	local missing_required = {}
	for _, tool in ipairs(required_tools) do
		if vim.fn.executable(tool.name) == 1 then
			ok(tool.name .. " found - " .. tool.desc)
		else
			error(tool.name .. " not found - " .. tool.desc)
			table.insert(missing_required, tool.name)
		end
	end

	-- Check for optional Mason tools
	local optional_tools = {
		{ name = "npm", desc = "Required for pyright and Node-based LSPs" },
		{ name = "cargo", desc = "Optional for Rust-based Mason tools" },
		{ name = "go", desc = "Optional for Go-based Mason tools" },
	}

	local missing_optional = {}
	for _, tool in ipairs(optional_tools) do
		if vim.fn.executable(tool.name) == 1 then
			ok(tool.name .. " found - " .. tool.desc)
		else
			warn(tool.name .. " not found - " .. tool.desc)
			table.insert(missing_optional, tool.name)
		end
	end

	-- Tree-sitter parsers check
	start("Tree-sitter Parsers")

	local parser_dir = vim.fn.stdpath("data") .. "/lazy/nvim-treesitter/parser"
	if vim.fn.isdirectory(parser_dir) == 1 then
		local parser_count = #vim.fn.glob(parser_dir .. "/*.so", false, true)
		if parser_count > 0 then
			ok(string.format("%d compiled parsers found in %s", parser_count, parser_dir))
		else
			warn("No compiled parsers found - run :TSInstall to compile parsers")
		end
	else
		error("Parser directory not found at " .. parser_dir)
		info("Run :Lazy build nvim-treesitter to create parsers")
	end

	-- Mason LSP/formatter check
	start("Mason Tools")

	local mason_bin = vim.fn.stdpath("data") .. "/mason/bin"
	if vim.fn.isdirectory(mason_bin) == 1 then
		local expected_tools = { "lua-language-server", "stylua", "pyright", "black" }
		for _, tool in ipairs(expected_tools) do
			if vim.fn.executable(mason_bin .. "/" .. tool) == 1 then
				ok(tool .. " installed")
			else
				warn(tool .. " not installed - run :MasonInstall " .. tool)
			end
		end
	else
		info("Mason not initialized yet - will be set up on first :Mason command")
	end

	-- Installation suggestions
	if #missing_required > 0 or #missing_optional > 0 then
		start("Installation Suggestions")
		if #missing_required > 0 then
			info("Install required tools: sudo pacman -S " .. table.concat(missing_required, " "))
		end
		if #missing_optional > 0 then
			info("Install optional tools: sudo pacman -S " .. table.concat(missing_optional, " "))
		end
	end
end

return M
