-- Neovim Minimal Config 🌃 with Smart Find, Hyper Escape, and TokyoNightDeep Theme

-- ==============================================
-- 🛠️ Core Settings
-- ==============================================
vim.g.mapleader = " " -- Space as leader key

-- Sensible defaults
vim.o.number = true
vim.o.relativenumber = true
vim.o.cursorline = true
vim.o.expandtab = true
vim.o.shiftwidth = 4
vim.o.tabstop = 4
vim.o.smartindent = true

vim.o.clipboard = "unnamedplus"

vim.o.ignorecase = true
vim.o.smartcase = true
vim.o.incsearch = true
vim.o.hlsearch = true

vim.o.splitbelow = true
vim.o.splitright = true

vim.o.updatetime = 300
vim.o.timeoutlen = 500

-- ==============================================
-- 🚀 Plugin Manager: lazy.nvim
-- ==============================================
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
  -- Treesitter for syntax highlighting
  { "nvim-treesitter/nvim-treesitter", build = ":TSUpdate" },

  -- Telescope (fuzzy finder)
  { "nvim-telescope/telescope.nvim", tag = "0.1.4", dependencies = { "nvim-lua/plenary.nvim" } },

  -- Telescope FZF Native (super fast sorter)
  {
    "nvim-telescope/telescope-fzf-native.nvim",
    build = "make",
    cond = function()
      return vim.fn.executable("make") == 1
    end,
  },

  -- [Future] Add LSP setup here
  -- { "neovim/nvim-lspconfig" },

  -- [Future] Add Completion setup here
  -- { "hrsh7th/nvim-cmp" },

  -- [Future] Git integrations
  -- { "lewis6991/gitsigns.nvim" },
})

-- ==============================================
-- 🌳 Treesitter Setup
-- ==============================================
require('nvim-treesitter.configs').setup {
  ensure_installed = { "python", "lua", "vim" },
  highlight = { enable = true },
}

-- ==============================================
-- 🔭 Telescope Setup
-- ==============================================

-- Build ignore patterns dynamically
local ignore_patterns = {}
local ignore_file = vim.fn.expand("~/.config/ignore/ignore")
local file = io.open(ignore_file, "r")
if file then
  for line in file:lines() do
    if #line > 0 then
      -- Strip asterisks and escape special characters
      line = line:gsub("%*", ""):gsub("%.", "%%."):gsub("%-", "%%-")
      table.insert(ignore_patterns, line)
    end
  end
  file:close()
end

-- Final Telescope setup
require('telescope').setup({
  defaults = {
    file_ignore_patterns = ignore_patterns,
    vimgrep_arguments = {
      "rg",
      "--color=never",
      "--no-heading",
      "--with-filename",
      "--line-number",
      "--column",
      "--smart-case",
      "--hidden",
      "--glob", "!.git/*",
    },
  },
  pickers = {
    find_files = {
      hidden = true,
      follow = true,
    },
  },
})

require('telescope').load_extension('fzf')

-- ==============================================
-- 📦 [Future] Additional Plugin Configs
-- ==============================================

-- Placeholder for configuring gitsigns.nvim, lualine.nvim, nvim-cmp, etc.

-- Example:
-- require('gitsigns').setup({})
-- require('lualine').setup({})

-- ==============================================
-- 🧠 Keymaps
-- ==============================================

-- --- Nordic Normal Mode Boost Pack (init.lua version) ---
-- Map ¤ (Shift+4) to move to end of line ($)
vim.keymap.set('n', '¤', '$', { noremap = true })
-- Map & (Shift+6) to move to first non-blank (^)
vim.keymap.set('n', '&', '^', { noremap = true })
-- Map ½ (Shift+backtick) to toggle case (~)
vim.keymap.set('n', '½', '~', { noremap = true })
-- Map ´ (dead accent next to backspace) to auto-indent (=)
vim.keymap.set('n', '´', '=', { noremap = true })
-- Map Ä (Shift+Ä) to register prefix (")
vim.keymap.set('n', 'Ä', '"', { noremap = true })
-- Map ä (Shift+ä) to jump to mark (')
vim.keymap.set('n', 'ä', "'", { noremap = true })
-- Map å (where { lives) to {
vim.keymap.set('n', 'å', '{', { noremap = true })
vim.keymap.set('n', 'Å', '}', { noremap = true })
-- Map ¨ (where [ lives) to [
vim.keymap.set('n', '¨', '[', { noremap = true })
-- Map ^ (where ] lives) to ]
vim.keymap.set('n', '^', ']', { noremap = true })

-- Double Space for Escape behavior
vim.keymap.set('i', '<Space><Space>', '<Esc>', { noremap = true, silent = true })
vim.keymap.set('v', '<Space><Space>', '<Esc>', { noremap = true, silent = true })
vim.keymap.set('n', '<Space><Space>', ':nohlsearch<CR>', { noremap = true, silent = true })

-- Telescope Smart Find
local function smart_find_files()
  local ok = pcall(require('telescope.builtin').git_files, { show_untracked = true })
  if not ok then
    require('telescope.builtin').find_files()
  end
end
vim.keymap.set('n', '<leader>f', smart_find_files, { desc = "Smart Find Files (Git aware)" })

-- Telescope Live Grep
vim.keymap.set('n', '<leader>g', require('telescope.builtin').live_grep, { desc = "Live Grep" })

-- ==============================================
-- 🎨 Colorscheme
-- ==============================================
require("colors.tokyonight_deep").setup()
