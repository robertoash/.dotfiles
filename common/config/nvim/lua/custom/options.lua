--=============================================================================
-- BASIC SETTINGS
--=============================================================================
-- Leader key configuration
vim.g.mapleader = " "
vim.g.maplocalleader = " "
vim.g.have_nerd_font = true

-- Python provider configuration
vim.g.python3_host_prog = vim.fn.exepath("python3")

-- Performance and responsiveness
vim.o.timeout = true
vim.o.timeoutlen = 300
-- Disable swap files
vim.opt.swapfile = false

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

-- Clipboard: Use OSC 52 for SSH sessions, system clipboard otherwise
vim.schedule(function()
	-- Detect if we're in an SSH session
	local in_ssh = vim.env.SSH_TTY ~= nil or vim.env.SSH_CONNECTION ~= nil

	if in_ssh then
		-- Use OSC 52 for copying only (WezTerm doesn't support OSC 52 paste yet)
		-- To paste from local clipboard, use WezTerm's paste (middle-click or Ctrl+Shift+V)
		local function paste()
			return {
				vim.split(vim.fn.getreg(""), "\n"),
				vim.fn.getregtype(""),
			}
		end

		vim.g.clipboard = {
			name = "OSC 52",
			copy = {
				["+"] = require("vim.ui.clipboard.osc52").copy("+"),
				["*"] = require("vim.ui.clipboard.osc52").copy("*"),
			},
			paste = {
				["+"] = paste,
				["*"] = paste,
			},
		}
	else
		-- Use system clipboard for local sessions
		vim.o.clipboard = "unnamedplus"
	end
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

-- Termguicolors for colorizer
vim.o.termguicolors = true
-- Turn on language detection
vim.cmd("filetype plugin indent on")

-- Return the module (not necessary but good practice)
return {}
