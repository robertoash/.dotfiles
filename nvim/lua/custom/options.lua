--=============================================================================
-- BASIC SETTINGS
--=============================================================================
-- Leader key configuration
vim.g.mapleader = " "
vim.g.maplocalleader = " "
vim.g.have_nerd_font = true

-- Performance and responsiveness
vim.o.timeout = true
vim.o.timeoutlen = 300

--=============================================================================
-- EDITOR OPTIONS
--=============================================================================
-- Line numbers and UI
vim.o.number = true
vim.o.relativenumber = true
vim.o.mouse = "" -- "a" to activate
vim.o.showmode = false
vim.o.signcolumn = "yes"
vim.o.cursorline = true
vim.o.scrolloff = 10
vim.o.list = true
vim.opt.listchars = { tab = "» ", trail = "·", nbsp = "␣" }

-- Performance and responsiveness
vim.o.updatetime = 250

-- Clipboard
vim.schedule(function()
	vim.o.clipboard = "unnamedplus"
end)

-- Search and substitution
vim.o.ignorecase = true
vim.o.smartcase = true
vim.o.inccommand = "split"

-- Undo and history
vim.o.undofile = true
vim.o.confirm = true

-- Window and splits
vim.o.splitright = true
vim.o.splitbelow = true

-- Indentation and tabs
vim.o.expandtab = true
vim.o.shiftwidth = 4
vim.o.tabstop = 4
vim.o.smartindent = true
vim.o.breakindent = true

-- Return the module (not necessary but good practice)
return {}