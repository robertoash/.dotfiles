--=============================================================================
-- NEOVIM CONFIGURATION
--=============================================================================

-- Load custom configurations
require("custom.options")

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
-- NEOVIDE SETUP
--=============================================================================
if vim.g.neovide then
	vim.g.neovide_padding_top = 20
	vim.g.neovide_padding_bottom = 10
	vim.g.neovide_padding_right = 20
	vim.g.neovide_padding_left = 20
	vim.g.neovide_opacity = 0.8
	vim.g.neovide_normal_opacity = 0.8
	vim.g.neovide_cursor_animation_length = 0.150
end

--=============================================================================
-- PLUGINS
--=============================================================================
require("lazy").setup({
	---------------------------
	-- PLUGIN IMPORTS
	---------------------------
	{ import = "plugins.utility" },
	{ import = "plugins.ai" },
	{ import = "plugins.telescope" },
	{ import = "plugins.lsp" },
	{ import = "plugins.formatting" },
	{ import = "plugins.obsidian" },
	{ import = "plugins.ui" },
	{ import = "plugins.treesitter" },
	{ import = "plugins.comment" },
	{ import = "plugins.snacks" },
}, {
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
-- KEYBOARD LAYOUT LUA
--=============================================================================
require("custom.keyboard_layout_remaps")

--=============================================================================
-- CUSTOM COMMANDS
--=============================================================================
require("custom.commands")

--=============================================================================
-- CUSTOM KEYMAPS
--=============================================================================
require("custom.keymaps")
