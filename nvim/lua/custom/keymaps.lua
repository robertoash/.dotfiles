--=============================================================================
-- KEYMAPS
--=============================================================================
-- All plugin-specific keymaps are now managed here, not in plugin configs
-- Note: Additional plugin-specific keymaps can be found in their respective plugin configs

--==========================================================================
--                          PLUGIN MAPPINGS
--==========================================================================

-- Which-key group registration (popup organization)
local wk_ok, wk = pcall(require, "which-key")
if wk_ok then
	wk.add({
		{ "<leader>a", group = "[A]vante AI", mode = { "n", "v" } },
		{ "<leader>b", group = "[B]uffer Operations", mode = { "n", "v" } },
		{ "<leader>b/", group = "[B]uffer Na[V]igation", mode = { "n", "v" } },
		{ "<leader>bc", group = "[B]uffer [C]lose", mode = { "n", "v" } },
		{ "<leader>c", group = "[C]laude Code", mode = { "n", "v" } },
		{ "<leader>d", group = "Working [D]ir", mode = { "n", "v" } },
		{ "<leader>f", group = "[F]ind", mode = { "n", "v" } },
		{ "<leader>fr", group = "Find and [R]eplace", mode = { "n", "v" } },
		{ "<leader>g", group = "[G]it", mode = { "n", "v" } },
		{ "<leader>h", group = "[H]arpoon", mode = { "n", "v" } },
		{ "<leader>m", group = "[M]ulticursor", mode = { "n", "v" } },
		{ "<leader>n", group = "[N]oice UI", mode = { "n", "v" } },
		{ "<leader>o", group = "[O]il File Manager", mode = { "n", "v" } },
		{ "<leader>p", group = "[P]airs Toggle", mode = { "n", "v" } },
		{ "<leader>q", group = "[Q]uickfix", mode = { "n", "v" } },
		{ "<leader>s", group = "[S]earch", mode = { "n", "v" } },
		{ "<leader>s/", group = "[S]earch [/] within files", mode = { "n", "v" } },
		{ "<leader>t", group = "[T]erminal", mode = { "n", "v" } },
		{ "<leader>t/", group = "[T]erminal [/] management", mode = { "n", "v" } },
		{ "<leader>u", group = "[U]ndo Tree", mode = { "n", "v" } },
		{ "<leader>x", group = "Trouble Diagnostics", mode = { "n", "v" } },
		{ "<leader>y", group = "[Y]azi File Manager", mode = { "n", "v" } },
		{ "<leader>=", group = "[=] Apply format", mode = { "n" } },
		{ "<leader>-", group = "Window splits [|]", mode = { "n", "v" } },
	})
end

local working_dir_mappings = {
	{
		"n",
		"<leader>d.",
		":cd %:h | pwd<CR>",
		{ desc = "CWD here [.]" },
	},
	{
		"n",
		"<leader>dr",
		function()
			local git_root = vim.fn.system("git rev-parse --show-toplevel 2>/dev/null"):gsub("\n", "")
			if vim.v.shell_error == 0 then
				vim.cmd("cd " .. vim.fn.fnameescape(git_root))
				print(git_root)
			else
				print("Not in a git repository.")
			end
		end,
		{ desc = "CWD to Git [R]oot" },
	},
}
-- Claude Code (AI plugin)
local claude_mappings = {
	{
		"n",
		"<leader>cc",
		function()
			vim.cmd("ClaudeCode")
		end,
		{ desc = "[C]laude [C]ode" },
	},
	{
		"n",
		"<leader>cr",
		function()
			vim.cmd("ClaudeCodeResume")
		end,
		{ desc = "[C]laude [R]esume" },
	},
}

-- Lazygit
local lazygit_mappings = {
	{
		"n",
		"<leader>gg",
		function()
			Snacks.lazygit()
		end,
		{ desc = "Lazy[GG]it" },
	},
}

-- Conform.nvim (formatting)
local format_mappings = {
	{
		"n",
		"<leader>=",
		function()
			local ok, conform = pcall(require, "conform")
			if ok then
				conform.format({ async = true, lsp_format = "fallback" })
			end
		end,
		{ desc = "Apply [=] format" },
	},
}

-- Flash.nvim: fast navigation
local flash_mappings = {
	{
		{ "n", "x", "o" },
		"<leader>ff",
		function()
			local ok, flash = pcall(require, "flash")
			if ok then
				flash.jump()
			end
		end,
		{ desc = "[F]lash jump" },
	},
	{
		{ "n", "x", "o" },
		"<leader>f.",
		function()
			local ok, flash = pcall(require, "flash")
			if ok then
				flash.jump({ search = { mode = "search", max_length = 1 } })
			end
		end,
		{ desc = "Flash jump single char [.]" },
	},
}

-- Telescope keymaps (migrated from plugin config)
local telescope_mappings = {
	{
		"n",
		"<leader>sb",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.buffers()
			end
		end,
		{ desc = "[S]earch [B]uffers" },
	},
	{
		"n",
		"<leader>sf",
		function()
			local ok, ext = pcall(require, "telescope")
			if ok and ext.extensions and ext.extensions.frecency then
				ext.extensions.frecency.frecency({ hidden = true, no_ignore = true })
			end
		end,
		{ desc = "[S]earch [F]recency" },
	},
	{
		"n",
		"<leader>sd",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.diagnostics()
			end
		end,
		{ desc = "[S]earch [D]iagnostics" },
	},
	{
		"n",
		"<leader>ss",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.find_files()
			end
		end,
		{ desc = "[SS]earch files" },
	},
	{
		"n",
		"<leader>sg",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.live_grep()
			end
		end,
		{ desc = "[S]earch [G]rep" },
	},
	{
		"n",
		"<leader>sh",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.help_tags()
			end
		end,
		{ desc = "[S]earch [H]elp" },
	},
	{
		"n",
		"<leader>sk",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.keymaps()
			end
		end,
		{ desc = "[S]earch [K]eymaps" },
	},
	{
		"n",
		"<leader>sn",
		function()
			-- Use regular find_files but in nvim config directory - more reliable scoping
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.find_files({
					cwd = vim.fn.expand("~/.config/nvim"),
					hidden = true,
					no_ignore_parent = true,
					prompt_title = "Find Neovim Files",
				})
			end
		end,
		{ desc = "[S]earch [N]eovim files" },
	},
	{
		"n",
		"<leader>sr",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.resume()
			end
		end,
		{ desc = "[S]earch [R]esume" },
	},
	{
		"n",
		"<leader>s/a",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.live_grep({ grep_open_files = true, prompt_title = "Live Grep in Open Files" })
			end
		end,
		{ desc = "[S]earch [/] [A]ll Open Files" },
	},
	{
		"n",
		"<leader>s/.",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.current_buffer_fuzzy_find(
					require("telescope.themes").get_dropdown({ winblend = 10, previewer = false })
				)
			end
		end,
		{ desc = "Fuzzy [S]earch [/] current buffer [.]" },
	},
	{
		"n",
		"<leader>sw",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.grep_string()
			end
		end,
		{ desc = "[S]earch current [W]ord" },
	},
	vim.keymap.set("n", "<leader>z", ":Telescope zoxide list<CR>", { desc = "Zoxide directories" }),
}

--==========================================================================
--                          CUSTOM KEYMAPS
--==========================================================================

-- Basic movement and operations
local basic_mappings = {
	{ "n", "<Esc>", "<cmd>nohlsearch<CR>", nil },
	{ "t", "<Esc><Esc>", "<C-\\><C-n>", { desc = "Exit terminal mode" } },
}

-- Disable arrow keys in normal mode
local arrow_mappings = {
	{ "n", "<left>", "<cmd>echo 'Use h to move!!'<CR>", { desc = nil } },
	{ "n", "<right>", "<cmd>echo 'Use l to move!!'<CR>", { desc = nil } },
	{ "n", "<up>", "<cmd>echo 'Use k to move!!'<CR>", { desc = nil } },
	{ "n", "<down>", "<cmd>echo 'Use j to move!!'<CR>", { desc = nil } },
}

-- Faster navigation
local fastnav_mappings = {
	{ "n", "<C-j>", "10j", { desc = "Move down 10 times" } },
	{ "v", "<C-j>", "10j", { desc = "Move down 10 times" } },
	{ "n", "<C-k>", "10k", { desc = "Move up 10 times" } },
	{ "v", "<C-k>", "10k", { desc = "Move up 10 times" } },
}

-- Fast edit mappings
local fastedit_mappings = {
	{ "n", "<A-S-j>", ":m .+1<CR>==", { noremap = true, silent = true } },
	{ "n", "<A-S-k>", ":m .-2<CR>==", { noremap = true, silent = true } },
	{ "v", "<A-S-j>", ":m '>+1<CR>gv=gv", { noremap = true, silent = true } },
	{ "v", "<A-S-k>", ":m '<-2<CR>gv=gv", { noremap = true, silent = true } },
}

-- Diagnostics
local diagnostic_mappings = {
	{ "n", "<leader>qd", vim.diagnostic.setloclist, { desc = "Open [Q]uickfix [D]iagnostic list" } },
}

-- Select whole document
local selectall_mappings = {
	{ "n", "<leader>%", "<cmd>normal! ggVG<cr>", { noremap = true, desc = "[%] Select entire buffer" } },
}

-- Find and replace mappings
local find_replace_mappings = {
	{ "n", "<leader>fr.", ":s//g<Left><Left>", { desc = "Find and replace on current line [.]" } },
	{ "v", "<leader>fr.", ":s//g<Left><Left>", { desc = "Find and replace in selection [.]" } },
	{ "n", "<leader>fr%", ":%s//g<Left><Left>", { desc = "Find and replace in entire document [%]" } },
}

-- Buffer and Window Management Keybinds

-- Window creation and closing using <leader>-
local window_operations_mappings = {
	-- Window creation (splits)
	{ "n", "<leader>-s", "<C-w>s", { desc = "Split window horizontally" } },
	{ "n", "<leader>-v", "<C-w>v", { desc = "Split window vertically" } },
	-- Window closing
	{ "n", "<leader>-c", "<C-w>c", { desc = "Close current window/split" } },
}

-- Window navigation using Alt+hjkl (fish compatible)
local window_navigation_mappings = {
	{ "n", "<A-h>", "<C-w>h", { desc = "Go to left window" } },
	{ "n", "<A-j>", "<C-w>j", { desc = "Go to lower window" } },
	{ "n", "<A-k>", "<C-w>k", { desc = "Go to upper window" } },
	{ "n", "<A-l>", "<C-w>l", { desc = "Go to right window" } },
	{ "n", "<A-n>", "<C-w>w", { desc = "Go to next window" } },
}

local snacks_terminal_navigation = {
	{ "t", "<A-h>", "<C-\\><C-n><C-w>h", { desc = "Go to left window" } },
	{ "t", "<A-j>", "<C-\\><C-n><C-w>j", { desc = "Go to lower window" } },
	{ "t", "<A-k>", "<C-\\><C-n><C-w>k", { desc = "Go to upper window" } },
	{ "t", "<A-l>", "<C-\\><C-n><C-w>l", { desc = "Go to right window" } },
	{ "t", "<A-n>", "<C-\\><C-n><C-w>w", { desc = "Go to next window" } },
}

-- Apply terminal navigation keymaps to all terminal buffers (including snacks)
vim.api.nvim_create_autocmd("TermOpen", {
	callback = function()
		for _, mapping in ipairs(snacks_terminal_navigation) do
			local mode, lhs, rhs, opts = mapping[1], mapping[2], mapping[3], mapping[4]
			vim.keymap.set(mode, lhs, rhs, vim.tbl_extend("force", opts, { buffer = true }))
		end
	end,
	desc = "Set window navigation keymaps for terminal buffers",
})

-- Buffer management keybinds using <leader>b
local buffer_mappings = {
	-- Common operations (direct access)
	{ "n", "<leader>bn", ":enew<CR>", { desc = "[B]uffer [N]ew" } },
	{ "n", "<leader>bl", ":ls<CR>", { desc = "[B]uffer [L]ist" } },

	-- Navigation sub-group
	{ "n", "<leader>bvj", ":bnext<CR>", { desc = "[B]uffer Na[V]igation: Next [J]" } },
	{ "n", "<leader>bvk", ":bprev<CR>", { desc = "[B]uffer Na[V]igation: Previous [K]" } },
	{ "n", "<leader>bvl", ":blast<CR>", { desc = "[B]uffer Na[V]igation: [L]ast" } },
	{ "n", "<leader>bvf", ":bfirst<CR>", { desc = "[B]uffer Na[V]igation: [F]irst" } },

	-- Closing sub-group
	{ "n", "<leader>bcc", ":bd<CR>", { desc = "[B]uffer [C]lose" } },
	{ "n", "<leader>bc!", ":bd!<CR>", { desc = "[B]uffer [C]lose force" } },
}

-- Delete to blackhole mappings
local delete_to_blackhole_mappings = {
	{ "n", "<leader>D", '"_d', { desc = "Delete to blackhole" } },
	{ "v", "<leader>D", '"_d', { desc = "Delete to blackhole" } },
	{ "n", "<leader>DD", '"_dd', { desc = "Delete line to blackhole" } },
}

local snacks_terminal_mappings = {
	-- Quick toggle (direct access)
	{
		"n",
		"<leader>tt",
		function()
			require("snacks.terminal").toggle()
		end,
		{ desc = "Terminal [T]oggle" },
	},

	-- Terminal management sub-group
	{
		"n",
		"<leader>t/f",
		function()
			require("snacks.terminal").toggle()
		end,
		{ desc = "Terminal [F]loating" },
	},
	{
		"n",
		"<leader>t/p",
		function()
			local pickers = require("telescope.pickers")
			local finders = require("telescope.finders")
			local conf = require("telescope.config").values
			local actions = require("telescope.actions")
			local action_state = require("telescope.actions.state")
			local terms = require("snacks.terminal").list()

			pickers
				.new({}, {
					prompt_title = "Terminal Buffers",
					finder = finders.new_table({
						results = terms,
						entry_maker = function(entry)
							return {
								value = entry,
								display = entry.name,
								ordinal = entry.name,
							}
						end,
					}),
					sorter = conf.generic_sorter({}),
					attach_mappings = function(prompt_bufnr, _)
						actions.select_default:replace(function()
							actions.close(prompt_bufnr)
							local selection = action_state.get_selected_entry().value
							selection:show()
						end)
						return true
					end,
				})
				:find()
		end,
		{ desc = "[T]erminal [/] pick" },
	},
}

--[[
=====================================================================
MINI.SURROUND KEYMAPS (handled by plugin setup)
=====================================================================
These mappings are set automatically by mini.surround.setup() and 
documented here for reference:

ADDING QUOTES/BRACKETS:
  saiw"     - surround inner word with double quotes
  saiw'     - surround inner word with single quotes  
  saiw)     - surround inner word with parentheses
  saip"     - surround inner paragraph with double quotes
  
REPLACING QUOTES/BRACKETS:
  sr'"      - replace single quotes with double quotes
  sr")      - replace double quotes with parentheses
  sr)(      - replace ) with (
  
DELETING QUOTES/BRACKETS:
  sd"       - delete double quotes
  sd'       - delete single quotes
  sd)       - delete parentheses
  
VISUAL MODE:
  Select text → sa" - surround selection with double quotes
  
OTHER OPERATIONS:
  sf"       - find next double quote (right)
  sF"       - find previous double quote (left)  
  sh        - highlight current surrounding
  sn        - update n_lines for search
=====================================================================
--]]

-- Mini.splitjoin keymaps
local mini_splitjoin_mappings = {
	{
		{ "n", "x" },
		"<leader>kj",
		function()
			require("mini.splitjoin").join()
		end,
		{ desc = "Splitjoin [j]oin" },
	},
	{
		{ "n", "x" },
		"<leader>kk",
		function()
			require("mini.splitjoin").split()
		end,
		{ desc = "Splitjoin split [k]" },
	},
}

-- Noice.nvim keymaps
local noice_mappings = {
	{
		"n",
		"<leader>nd",
		function()
			require("noice").cmd("dismiss")
		end,
		{ desc = "Noice [D]ismiss all" },
	},
	{
		"n",
		"<leader>nh",
		function()
			require("noice").cmd("history")
		end,
		{ desc = "Noice [H]istory" },
	},
	{
		"n",
		"<leader>nl",
		function()
			require("noice").cmd("last")
		end,
		{ desc = "Noice [L]ast message" },
	},
	{
		"n",
		"<leader>ne",
		function()
			require("noice").cmd("errors")
		end,
		{ desc = "Noice [E]rrors" },
	},
	{
		"n",
		"<leader>nt",
		function()
			require("noice").cmd("telescope")
		end,
		{ desc = "Noice [T]elescope" },
	},
}

-- nvim-autopairs keymaps
local autopairs_mappings = {
	{
		"n",
		"<leader>pt",
		function()
			local autopairs = require("nvim-autopairs")
			if autopairs.state.disabled then
				autopairs.enable()
				vim.notify("Autopairs enabled", vim.log.levels.INFO)
			else
				autopairs.disable()
				vim.notify("Autopairs disabled", vim.log.levels.INFO)
			end
		end,
		{ desc = "Pairs [T]oggle" },
	},
}

-- Yazi.nvim keymaps (based on yazi config)
local yazi_mappings = {
	{
		{ "n", "v" },
		"<leader>yy",
		function()
			require("yazi").yazi()
		end,
		{ desc = "Open [Y]azi at current file" },
	},
	{
		"n",
		"<leader>yw",
		function()
			require("yazi").yazi(nil, vim.fn.getcwd())
		end,
		{ desc = "[Y]azi in current [W]orking directory" },
	},
	{
		"n",
		"<leader>y.",
		function()
			require("yazi").yazi(nil, vim.fn.expand("%:p:h"))
		end,
		{ desc = "[Y]azi [R]eveal current file" },
	},
}

-- Oil.nvim keymaps (yazi-like navigation)
local oil_mappings = {
	{
		"n",
		"<leader>oo",
		function()
			require("oil").open()
		end,
		{ desc = "[O]il [O]pen parent directory" },
	},
	{
		"n",
		"<leader>of",
		function()
			require("oil").open_float()
		end,
		{ desc = "[O]il [F]loating window" },
	},
	{
		"n",
		"<leader>o.",
		function()
			require("oil").open(vim.fn.expand("%:p:h"))
		end,
		{ desc = "[O]il [R]eveal current file" },
	},
	{
		"n",
		"-",
		function()
			require("oil").open()
		end,
		{ desc = "Open parent directory" },
	},
}

-- UndoTree keymaps
local undotree_mappings = {
	{
		"n",
		"<leader>uu",
		function()
			vim.cmd("UndotreeToggle")
		end,
		{ desc = "[U]ndo tree toggle" },
	},
	{
		"n",
		"<leader>uf",
		function()
			vim.cmd("UndotreeFocus")
		end,
		{ desc = "[U]ndo tree [F]ocus" },
	},
	{
		"n",
		"<F5>",
		function()
			vim.cmd("UndotreeToggle")
		end,
		{ desc = "UndoTree toggle" },
	},
}

-- Multicursor keymaps
local multicursor_mappings = {
	-- Toggle and clear operations
	{
		{ "n", "x" },
		"<leader>mm",
		function()
			local mc = require("multicursor-nvim")
			mc.toggleCursor()
		end,
		{ desc = "Toggle [m]ulticursor" },
	},
	-- Advanced operations
	{
		{ "n", "x" },
		"<leader>m*",
		function()
			local mc = require("multicursor-nvim")
			mc.matchAllAddCursors()
		end,
		{ desc = "Match [*] all add cursors" },
	},
	{
		"n",
		"<leader>ma",
		function()
			local mc = require("multicursor-nvim")
			mc.alignCursors()
		end,
		{ desc = "[A]lign cursors" },
	},
	{
		"n",
		"<leader>mr",
		function()
			local mc = require("multicursor-nvim")
			mc.restoreCursors()
		end,
		{ desc = "[R]estore cursors" },
	},
}

-- Harpoon keymaps
local harpoon_mappings = {
	{
		"n",
		"<leader>ha",
		function()
			local ok, harpoon = pcall(require, "harpoon")
			if ok then
				harpoon:list():add()
			end
		end,
		{ desc = "[H]arpoon [A]dd file" },
	},
	{
		"n",
		"<leader>hh",
		function()
			local ok, harpoon = pcall(require, "harpoon")
			if ok then
				harpoon.ui:toggle_quick_menu(harpoon:list())
			end
		end,
		{ desc = "[H]arpoon menu" },
	},
	-- Quick navigation to files 1-4 using Ctrl+Shift+uiop
	{
		"n",
		"<C-S-u>",
		function()
			local ok, harpoon = pcall(require, "harpoon")
			if ok then
				harpoon:list():select(1)
			end
		end,
		{ desc = "Harpoon file 1" },
	},
	{
		"n",
		"<C-S-i>",
		function()
			local ok, harpoon = pcall(require, "harpoon")
			if ok then
				harpoon:list():select(2)
			end
		end,
		{ desc = "Harpoon file 2" },
	},
	{
		"n",
		"<C-S-o>",
		function()
			local ok, harpoon = pcall(require, "harpoon")
			if ok then
				harpoon:list():select(3)
			end
		end,
		{ desc = "Harpoon file 3" },
	},
	{
		"n",
		"<C-S-p>",
		function()
			local ok, harpoon = pcall(require, "harpoon")
			if ok then
				harpoon:list():select(4)
			end
		end,
		{ desc = "Harpoon file 4" },
	},
	-- Navigate through the list with Ctrl+Shift+[] (brackets)
	{
		"n",
		"<C-S-[>",
		function()
			local ok, harpoon = pcall(require, "harpoon")
			if ok then
				harpoon:list():prev()
			end
		end,
		{ desc = "Harpoon previous" },
	},
	{
		"n",
		"<C-S-]>",
		function()
			local ok, harpoon = pcall(require, "harpoon")
			if ok then
				harpoon:list():next()
			end
		end,
		{ desc = "Harpoon next" },
	},
}

-- Trouble.nvim keymaps
local trouble_mappings = {
	{
		"n",
		"<leader>xx",
		function()
			vim.cmd("Trouble diagnostics toggle")
		end,
		{ desc = "Diagnostics (Trouble)" },
	},
	{
		"n",
		"<leader>xX",
		function()
			vim.cmd("Trouble diagnostics toggle filter.buf=0")
		end,
		{ desc = "Buffer Diagnostics (Trouble)" },
	},
	{
		"n",
		"<leader>xs",
		function()
			vim.cmd("Trouble symbols toggle focus=false")
		end,
		{ desc = "Symbols (Trouble)" },
	},
	{
		"n",
		"<leader>xl",
		function()
			vim.cmd("Trouble lsp toggle focus=false win.position=right")
		end,
		{ desc = "LSP Definitions / references / ... (Trouble)" },
	},
	{
		"n",
		"<leader>xL",
		function()
			vim.cmd("Trouble loclist toggle")
		end,
		{ desc = "Location List (Trouble)" },
	},
	{
		"n",
		"<leader>xQ",
		function()
			vim.cmd("Trouble qflist toggle")
		end,
		{ desc = "Quickfix List (Trouble)" },
	},
}

-- =====================
-- Keymap binding section
-- =====================

local function set_keymaps(mappings)
	for _, map in ipairs(mappings) do
		local mode, lhs, rhs, opts = map[1], map[2], map[3], map[4]
		if type(mode) == "table" then
			vim.keymap.set(mode, lhs, rhs, opts or {})
		else
			vim.keymap.set(mode, lhs, rhs, opts or {})
		end
	end
end

set_keymaps(claude_mappings)
set_keymaps(format_mappings)
set_keymaps(basic_mappings)
set_keymaps(arrow_mappings)

-- Hardtime toggle for when you need to browse/explore
vim.keymap.set("n", "<leader>th", function()
	require("hardtime").toggle()
end, { desc = "[T]oggle [H]ardtime" })
set_keymaps(fastnav_mappings)
set_keymaps(fastedit_mappings)
set_keymaps(window_operations_mappings)
set_keymaps(window_navigation_mappings)
set_keymaps(buffer_mappings)
set_keymaps(diagnostic_mappings)
set_keymaps(selectall_mappings)
set_keymaps(flash_mappings)
set_keymaps(telescope_mappings)
set_keymaps(delete_to_blackhole_mappings)
set_keymaps(snacks_terminal_mappings)
set_keymaps(lazygit_mappings)
set_keymaps(mini_splitjoin_mappings)
set_keymaps(noice_mappings)
set_keymaps(autopairs_mappings)
set_keymaps(find_replace_mappings)
set_keymaps(yazi_mappings)
set_keymaps(oil_mappings)
set_keymaps(undotree_mappings)
set_keymaps(harpoon_mappings)
set_keymaps(multicursor_mappings)
set_keymaps(trouble_mappings)
set_keymaps(working_dir_mappings)

return {}
