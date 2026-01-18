--=============================================================================
-- NEOVIM CONFIGURATION
--=============================================================================

-- Load custom configurations
require("custom.options")
require("custom.autocmds")

--=============================================================================
-- LAZY.NVIM SETUP (PLUGIN MANAGER)
--=============================================================================
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
	local lazyrepo = "https://github.com/folke/lazy.nvim.git"
	local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
	if vim.v.shell_error ~= 0 then
		error("Error cloning lazy.nvim:\n" .. out)
	end
end

---@type vim.Option
local rtp = vim.opt.rtp
rtp:prepend(lazypath)

--=============================================================================
-- MACHINE DETECTION
--=============================================================================
local function is_work_mac()
	local hostname = vim.fn.hostname()
	return hostname:match("^rash%-workmbp") ~= nil
end

--=============================================================================
-- PLUGINS
--=============================================================================
local plugins = {
	---------------------------
	-- PLUGIN IMPORTS
	---------------------------
	-- { import = "plugins.hardtime" },
	{ import = "plugins.autopairs" },
	{ import = "plugins.blink-cmp" },
	{ import = "plugins.claudecode" },
	{ import = "plugins.colorizer" },
	{ import = "plugins.comment" },
	{ import = "plugins.conform" },
	{ import = "plugins.diagram" },
	{ import = "plugins.flash" },
	{ import = "plugins.follow-md-links" },
	{ import = "plugins.git-conflict" },
	{ import = "plugins.gitsigns" },
	{ import = "plugins.harpoon" },
	{ import = "plugins.image" },
	{ import = "plugins.lazydev" },
	{ import = "plugins.lualine" },
	{ import = "plugins.mini" },
	{ import = "plugins.multicursors" },
	{ import = "plugins.noice" },
	{ import = "plugins.nvim-lspconfig" },
	{ import = "plugins.obsidian" },
	{ import = "plugins.oil" },
	{ import = "plugins.render-markdown" },
	{ import = "plugins.snacks" },
	{ import = "plugins.telescope" },
	{ import = "plugins.todo-comments" },
	{ import = "plugins.treesitter" },
	{ import = "plugins.trouble" },
	{ import = "plugins.undotree" },
	{ import = "plugins.vim-pencil" },
	{ import = "plugins.which-key" },
	{ import = "plugins.wrapwidth" },
	{ import = "plugins.yanky" },
	{ import = "plugins.yazi" },
}

-- Conditionally import work-specific plugins
if is_work_mac() then
	table.insert(plugins, { import = "plugins.dbtpal" })
	table.insert(plugins, { import = "plugins.dadbod" })
end

require("lazy").setup(plugins, {
	ui = {
		icons = vim.g.have_nerd_font and {} or {
			cmd = "⌘",
			config = "🛠",
			event = "📅",
			ft = "📂",
			init = "⚙",
			keys = "🗝",
			plugin = "🔌",
			runtime = "💻",
			require = "🌙",
			source = "📄",
			start = "🚀",
			task = "📌",
			lazy = "💤 ",
		},
	},
})

--=============================================================================
-- COLORSCHEME
--=============================================================================
pcall(require, "colors.tokyonight_deep")
require("colors.tokyonight_deep").setup()

--=============================================================================
-- CUSTOM OVERRIDES
--=============================================================================
pcall(require, "lsp.overrides.qutebrowser")

--=============================================================================
-- CUSTOM COMMANDS
--=============================================================================
require("custom.commands")

--=============================================================================
-- CUSTOM KEYMAPS
--=============================================================================
require("custom.keymaps")
