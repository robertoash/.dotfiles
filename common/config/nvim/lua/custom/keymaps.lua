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
		{ "<leader>-", group = "Window splits [-]", mode = { "n", "v" } },
		{ "<leader>0", group = "T[0]ggle", mode = { "n", "v" } },
		{ "<leader>=", group = "Apply format [=]", mode = { "n" } },
		{ "<leader>P", group = "[P]rint", mode = { "n", "v" } },
		{ "<leader>a", group = "[a]vante AI", mode = { "n", "v" } },
		{ "<leader>b", group = "[b]uffer Operations", mode = { "n", "v" } },
		{ "<leader>b/", group = "Buffer Navigation [/]", mode = { "n", "v" } },
		{ "<leader>bc", group = "Buffer [c]lose", mode = { "n", "v" } },
		{ "<leader>c", group = "[c]laude Code", mode = { "n", "v" } },
		{ "<leader>cd", group = "Claude Code [d]iff", mode = { "n", "v" } },
		{ "<leader>d", group = "Working [d]ir / DBT / Database", mode = { "n", "v" } },
		{ "<leader>db", group = "[d]ata[b]ase UI", mode = { "n", "v" } },
		{ "<leader>dr", group = "DBT [r]un", mode = { "n", "v" } },
		{ "<leader>dt", group = "DBT [t]est", mode = { "n", "v" } },
		{ "<leader>f", group = "[f]ind", mode = { "n", "v" } },
		{ "<leader>fr", group = "Find and [r]eplace", mode = { "n", "v" } },
		{ "<leader>g", group = "[g]it", mode = { "n", "v" } },
		{ "<leader>h", group = "[h]arpoon", mode = { "n", "v" } },
		{ "<leader>m", group = "[m]ulticursor", mode = { "n", "v" } },
		{ "<leader>n", group = "[n]oice UI", mode = { "n", "v" } },
		{ "<leader>o", group = "[o]il File Manager", mode = { "n", "v" } },
		{ "<leader>q", group = "[q]uickfix", mode = { "n", "v" } },
		{ "<leader>s", group = "[s]earch", mode = { "n", "v" } },
		{ "<leader>s/", group = "Search [/] within files", mode = { "n", "v" } },
		{ "<leader>t", group = "[t]erminal", mode = { "n", "v" } },
		{ "<leader>t/", group = "Terminal [/] management", mode = { "n", "v" } },
		{ "<leader>u", group = "[u]ndo Tree", mode = { "n", "v" } },
		{ "<leader>v", group = "Paste [v]", mode = { "n", "v" } },
		{ "<leader>x", group = "Trouble Diagnostics [x]", mode = { "n", "v" } },
		{ "<leader>y", group = "[y]azi File Manager", mode = { "n", "v" } },
		-- LSP keymaps (defined in nvim-lspconfig.lua via LspAttach autocmd)
		{ "g", group = "[g]oto / LSP", mode = { "n" } },
		{ "gr", group = "LSP [g]oto/[r]efactor", mode = { "n" } },
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
		"<leader>d/",
		function()
			local git_root = vim.fn.system("git rev-parse --show-toplevel 2>/dev/null"):gsub("\n", "")
			if vim.v.shell_error == 0 then
				vim.cmd("cd " .. vim.fn.fnameescape(git_root))
				print(git_root)
			else
				print("Not in a git repository.")
			end
		end,
		{ desc = "CWD to Git root [/]" },
	},
}

-- DBT mappings
local dbt_mappings = {
	{
		"n",
		"<leader>drf",
		"<cmd>DbtRun<cr>",
		{ desc = "DBT run [f]ile" },
	},
	{
		"n",
		"<leader>drp",
		"<cmd>DbtRunAll<cr>",
		{ desc = "DBT run [p]roject" },
	},
	{
		"n",
		"<leader>dtf",
		"<cmd>DbtTest<cr>",
		{ desc = "DBT test [f]ile" },
	},
	{
		"n",
		"<leader>dm",
		function()
			require("dbtpal.telescope").dbt_picker()
		end,
		{ desc = "DBT [m]odel picker" },
	},
}

-- Dadbod (Database UI) mappings
local dadbod_mappings = {
	{
		"n",
		"<leader>dbb",
		"<cmd>DBUIToggle<cr>",
		{ desc = "Toggle Data[b]ase UI" },
	},
}

local claudecode_mappings = {
	{
		"n",
		"<leader>cc",
		"<cmd>ClaudeCode<cr>",
		{ desc = "Claude [C]ode Inline" },
	},
	{
		"n",
		"<leader>cf",
		"<cmd>ClaudeCodeFocus<cr>",
		{ desc = "Claude Code [f]ocus" },
	},
	{
		"n",
		"<leader>ca",
		"<cmd>ClaudeCodeAdd %<cr>",
		{ desc = "Claude Code [a]dd buffer to context" },
	},
	{
		"v",
		"<leader>cs",
		"<cmd>ClaudeCodeSend<cr>",
		{ desc = "Claude Code [s]end selection" },
	},
	{
		"n",
		"<leader>cda",
		"<cmd>ClaudeCodeDiffAccept<cr>",
		{ desc = "Claude Code diff [a]ccept" },
	},
	{
		"n",
		"<leader>cdr",
		"<cmd>ClaudeCodeDiffReject<cr>",
		{ desc = "Claude Code diff [r]eject" },
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
		{ desc = "Lazy[g]it" },
	},
}

-- Conform.nvim (formatting)
local format_mappings = {
	{
		{ "n", "v" },
		"<leader>=",
		function()
			local ok, conform = pcall(require, "conform")
			if ok then
				-- In visual mode, format the selection
				-- In normal mode, format the whole document
				local mode = vim.fn.mode()
				if mode == "v" or mode == "V" or mode == "\22" then
					-- Visual mode: format selection using range
					conform.format({ async = true, lsp_format = "fallback" })
				else
					-- Normal mode: format entire buffer
					conform.format({ async = true, lsp_format = "fallback" })
				end
			end
		end,
		{ desc = "[=] Apply Format" },
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
		{ desc = "[f]lash jump" },
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
		"<leader>s/.",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.current_buffer_fuzzy_find(
					require("telescope.themes").get_dropdown({ winblend = 10, previewer = false })
				)
			end
		end,
		{ desc = "Fuzzy search current buffer [.]" },
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
		{ desc = "Search [a]ll open files" },
	},
	{
		"n",
		"<leader>sb",
		function()
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.buffers()
			end
		end,
		{ desc = "Search [b]uffers" },
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
		{ desc = "Search [d]iagnostics" },
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
		{ desc = "Search [f]recency" },
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
		{ desc = "Search [g]rep" },
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
		{ desc = "Search [h]elp" },
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
		{ desc = "Search [k]eymaps" },
	},
	{
		"n",
		"<leader>sn",
		function()
			-- Search in dotfiles directory
			local ok, builtin = pcall(require, "telescope.builtin")
			if ok then
				builtin.find_files({
					cwd = vim.fn.expand("~/.dotfiles"),
					hidden = true,
					no_ignore_parent = true,
					prompt_title = "Find Dotfiles Files",
				})
			end
		end,
		{ desc = "Search dotfiles" },
	},
	{
		"n",
		"<leader>sN",
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
		{ desc = "Search [N]eovim files" },
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
		{ desc = "Search [r]esume" },
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
		{ desc = "[s]earch files" },
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
		{ desc = "Search current [w]ord" },
	},
	{
		"n",
		"<leader>z",
		":Telescope zoxide list<CR>",
		{ desc = "[z]oxide directories" },
	},
}

--==========================================================================
--                          CUSTOM KEYMAPS
--==========================================================================

-- Basic movement and operations
local basic_mappings = {
	{ "n", "<Esc>", "<cmd>nohlsearch<CR>", nil },
	{ "t", "<Esc><Esc>", "<C-\\><C-n>", { desc = "Exit terminal mode" } },
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
	{ "n", "<leader>qd", vim.diagnostic.setloclist, { desc = "[q]uickfix diagnostics" } },
}

-- Select whole document
local selectall_mappings = {
	{ "n", "<leader>%", "<cmd>normal! ggVG<cr>", { noremap = true, desc = "Select entire buffer [%]" } },
}

-- Find and replace mappings
local find_replace_mappings = {
	{ "n", "<leader>fr", ":%s//g<Left><Left>", { desc = "Find and replace in entire document" } },
	{ "v", "<leader>fr", ":s//g<Left><Left>", { desc = "Find and replace in selection" } },
}

-- Printing mappings
local print_mappings = {
	{
		"n",
		"<leader>Pp",
		function()
			local filepath = vim.fn.expand("%:p")
			if filepath == "" then
				vim.notify("No file to print", vim.log.levels.ERROR)
				return
			end
			local cmd = string.format("lp -d Brother_DCP-L2530DW '%s'", filepath)
			local result = vim.fn.system(cmd)
			if vim.v.shell_error == 0 then
				vim.notify("Sent to printer: " .. vim.fn.expand("%:t"), vim.log.levels.INFO)
			else
				vim.notify("Print failed: " .. result, vim.log.levels.ERROR)
			end
		end,
		{ desc = "[p]rint current file" },
	},
	{
		"v",
		"<leader>Pp",
		function()
			-- Save selection to temp file and print
			local lines = vim.fn.getregion(vim.fn.getpos("v"), vim.fn.getpos("."))
			local tmpfile = vim.fn.tempname() .. ".txt"
			vim.fn.writefile(lines, tmpfile)
			local cmd = string.format("lp -d Brother_DCP-L2530DW '%s'", tmpfile)
			local result = vim.fn.system(cmd)
			if vim.v.shell_error == 0 then
				vim.notify("Sent selection to printer", vim.log.levels.INFO)
			else
				vim.notify("Print failed: " .. result, vim.log.levels.ERROR)
			end
			-- Clean up temp file
			vim.fn.delete(tmpfile)
		end,
		{ desc = "[p]rint selection" },
	},
}

-- Buffer and Window Management Keybinds

-- Window creation and closing using <leader>-
local window_operations_mappings = {
	-- Fast access with Alt keys
	{ "n", "<A-->", "<C-w>s", { desc = "Horizontal split" } },
	{ "n", "<A-+>", "<C-w>v", { desc = "Vertical split" } },

	-- Window creation (splits)
	{ "n", "<leader>-s", "<C-w>s", { desc = "[s]plit window horizontally" } },
	{ "n", "<leader>-v", "<C-w>v", { desc = "Split window [v]ertically" } },
	-- Window closing
	{ "n", "<leader>-c", "<C-w>c", { desc = "[c]lose current window/split" } },
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

-- Buffer management keybinds using <leader>b
local buffer_mappings = {
	-- Fast access with Alt keys
	{ { "n", "v" }, "<A->>", ":bnext<CR>", { desc = "Next buffer" } },
	{ { "n", "v" }, "<A-<>", ":bprev<CR>", { desc = "Previous buffer" } },
	{ { "n", "v" }, "<A-x>", ":bd<CR>", { desc = "Close buffer" } },

	-- Most common operations (short bindings)
	{ { "n", "v" }, "<leader>bd", ":bd<CR>", { desc = "[d]elete/close buffer" } },
	{ { "n", "v" }, "<leader>bq", ":bd!<CR>", { desc = "[q]uit buffer (force)" } },
	{ { "n", "v" }, "<leader>bn", ":bnext<CR>", { desc = "[n]ext buffer" } },
	{ { "n", "v" }, "<leader>bp", ":bprev<CR>", { desc = "[p]revious buffer" } },

	-- Less common operations
	{ { "n", "v" }, "<leader>b+", ":enew<CR>", { desc = "New buffer [+]" } },
	{ { "n", "v" }, "<leader>bl", ":ls<CR>", { desc = "[l]ist buffers" } },
	{ { "n", "v" }, "<leader>bf", ":bfirst<CR>", { desc = "[f]irst buffer" } },
	{ { "n", "v" }, "<leader>b$", ":blast<CR>", { desc = "Last buffer [$]" } },
}

-- Delete to blackhole mappings
local delete_to_blackhole_mappings = {
	{ "n", "<leader>D", '"_d', { desc = "Delete to blackhole" } },
	{ "v", "<leader>D", '"_d', { desc = "Delete to blackhole" } },
	{ "n", "<leader>DD", '"_dd', { desc = "Delete line to blackhole" } },
}

-- Yanky.nvim operations
local yanky_mappings = {
	{
		{ "n", "v", "x" },
		"<leader>vv",
		"<Plug>(YankyPutAfter)",
		{ desc = "Paste from yanky ring" },
	},
	{
		{ "n", "v", "x" },
		"<leader>vV",
		"<Plug>(YankyPutBefore)",
		{ desc = "Paste before from yanky ring" },
	},
	{
		{ "n", "x" },
		"<leader>vp",
		"<Plug>(YankyPreviousEntry)",
		{ desc = "Cycle to previous yanky entry" },
	},
	{
		{ "n", "x" },
		"<leader>vn",
		"<Plug>(YankyNextEntry)",
		{ desc = "Cycle to next yanky entry" },
	},
}

local snacks_terminal_mappings = {
	-- Quick toggle (direct access)
	{
		"n",
		"<leader>tt",
		function()
			require("snacks.terminal").toggle()
		end,
		{ desc = "Terminal [t]oggle" },
	},

	-- Terminal management sub-group
	{
		"n",
		"<leader>t/f",
		function()
			require("snacks.terminal").toggle()
		end,
		{ desc = "Terminal [f]loating" },
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
		{ desc = "Terminal [p]ick" },
	},
}

local hardtime_mappings = {
	{
		"n",
		"<leader>0h",
		function()
			require("hardtime").toggle()
		end,
		{ desc = "Toggle [h]ardtime" },
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
		{ desc = "[d]ismiss all" },
	},
	{
		"n",
		"<leader>nh",
		function()
			require("noice").cmd("history")
		end,
		{ desc = "[h]istory" },
	},
	{
		"n",
		"<leader>nl",
		function()
			require("noice").cmd("last")
		end,
		{ desc = "[l]ast message" },
	},
	{
		"n",
		"<leader>ne",
		function()
			require("noice").cmd("errors")
		end,
		{ desc = "[e]rrors" },
	},
	{
		"n",
		"<leader>nt",
		function()
			require("noice").cmd("telescope")
		end,
		{ desc = "[t]elescope" },
	},
}

-- nvim-autopairs keymaps
local autopairs_mappings = {
	{
		"n",
		"<leader>0p",
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
		{ desc = "Toggle [p]airs" },
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
		{ desc = "Open [y]azi" },
	},
	{
		"n",
		"<leader>yw",
		function()
			require("yazi").yazi(nil, vim.fn.getcwd())
		end,
		{ desc = "Yazi in current [w]orking directory" },
	},
	{
		"n",
		"<leader>y.",
		function()
			require("yazi").yazi(nil, vim.fn.expand("%:p:h"))
		end,
		{ desc = "Yazi reveal current file [.]" },
	},
}

-- Path yank keymap
local path_yank_mappings = {
	{
		"n",
		"<leader>py",
		function()
			local path = vim.fn.expand("%:p")
			vim.fn.setreg("+", path)
			vim.notify("Yanked: " .. path, vim.log.levels.INFO)
		end,
		{ desc = "[p]ath [y]ank (full)" },
	},
}

-- Oil.nvim keymaps (yazi-like navigation)
local oil_mappings = {
	{
		"n",
		"<leader>oo",
		function()
			-- Toggle Oil: close if in Oil buffer, open otherwise
			if vim.bo.filetype == "oil" then
				require("oil").close()
			else
				require("oil").open()
			end
		end,
		{ desc = "Oil [o]pen/toggle" },
	},
	{
		"n",
		"<leader>of",
		function()
			require("oil").open_float()
		end,
		{ desc = "Oil [f]loating window" },
	},
	{
		"n",
		"<leader>o.",
		function()
			require("oil").open(vim.fn.expand("%:p:h"))
		end,
		{ desc = "Oil reveal current file [.]" },
	},
	{
		"n",
		"-",
		function()
			require("oil").open()
		end,
		{ desc = "Open parent directory [-]" },
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
		{ desc = "[u]ndo tree toggle" },
	},
	{
		"n",
		"<leader>uf",
		function()
			vim.cmd("UndotreeFocus")
		end,
		{ desc = "Undo tree [f]ocus" },
	},
	{
		"n",
		"<F5>",
		function()
			vim.cmd("UndotreeToggle")
		end,
		{ desc = "Undo tree toggle" },
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
		{ desc = "Match all add cursors [*]" },
	},
	{
		"n",
		"<leader>ma",
		function()
			local mc = require("multicursor-nvim")
			mc.alignCursors()
		end,
		{ desc = "[a]lign cursors" },
	},
	{
		"n",
		"<leader>mr",
		function()
			local mc = require("multicursor-nvim")
			mc.restoreCursors()
		end,
		{ desc = "[r]estore cursors" },
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
		{ desc = "Harpoon [a]dd file" },
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
		{ desc = "[h]arpoon menu" },
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
		{ desc = "Diagnostics (Trouble) [x]" },
	},
	{
		"n",
		"<leader>xX",
		function()
			vim.cmd("Trouble diagnostics toggle filter.buf=0")
		end,
		{ desc = "Buffer Diagnostics (Trouble) [X]" },
	},
	{
		"n",
		"<leader>xs",
		function()
			vim.cmd("Trouble symbols toggle focus=false")
		end,
		{ desc = "[s]ymbols (Trouble)" },
	},
	{
		"n",
		"<leader>xl",
		function()
			vim.cmd("Trouble lsp toggle focus=false win.position=right")
		end,
		{ desc = "[l]sp definitions / references / ... (Trouble)" },
	},
	{
		"n",
		"<leader>xL",
		function()
			vim.cmd("Trouble loclist toggle")
		end,
		{ desc = "[L]ocation list (Trouble)" },
	},
	{
		"n",
		"<leader>xQ",
		function()
			vim.cmd("Trouble qflist toggle")
		end,
		{ desc = "[q]uickfix list (Trouble)" },
	},
}

-- Oil keymaps (for Oil's setup function)
local oil_keymaps = {
	["-"] = "actions.parent",
	["<C-c>"] = "actions.close",
	["<C-h>"] = "actions.select_split",
	["<C-l>"] = "actions.refresh",
	["<C-p>"] = "actions.preview",
	["<C-s>"] = "actions.select_vsplit",
	["<C-t>"] = "actions.select_tab",
	["<CR>"] = "actions.select",
	["_"] = "actions.open_cwd",
	["`"] = "actions.cd",
	["g."] = "actions.toggle_hidden",
	["g?"] = "actions.show_help",
	["g\\"] = "actions.toggle_trash",
	["gs"] = "actions.change_sort",
	["gx"] = "actions.open_external",
	["q"] = "actions.close",
	["~"] = "actions.tcd",
	-- Custom additions for more intuitive navigation
	["<BS>"] = "actions.parent",
	["H"] = "actions.parent",
	-- Custom action to add file to ClaudeCode context
	["<leader>ca"] = {
		callback = function()
			local oil = require("oil")
			local entry = oil.get_cursor_entry()
			local dir = oil.get_current_dir()
			if entry and dir then
				local full_path = dir .. entry.name
				-- Only add if it's a file (not a directory)
				if entry.type == "file" then
					vim.cmd("ClaudeCodeAdd " .. vim.fn.fnameescape(full_path))
					vim.notify("Added to Claude Code: " .. entry.name, vim.log.levels.INFO)
				else
					vim.notify("Cannot add directory to Claude Code", vim.log.levels.WARN)
				end
			end
		end,
		desc = "Add file to Claude Code context",
		mode = "n",
	},
}

-- Conflict marker keymaps (for buffers with git conflicts)
local conflict_marker_mappings = {
	{ "n", "co", "<cmd>Conflict ours<cr>", { desc = "Choose ours" } },
	{ "n", "ct", "<cmd>Conflict theirs<cr>", { desc = "Choose theirs" } },
	{ "n", "cb", "<cmd>Conflict both<cr>", { desc = "Choose both" } },
	{ "n", "c0", "<cmd>Conflict none<cr>", { desc = "Choose none" } },
	{ "n", "]x", "<cmd>Conflict next<cr>", { desc = "Next conflict" } },
	{ "n", "[x", "<cmd>Conflict prev<cr>", { desc = "Previous conflict" } },
}

-- Function to get Oil keymaps for the setup
local M = {}
function M.get_oil_keymaps()
	return oil_keymaps
end

--[[
    =====================================================================
    MARKDOWN LINK NAVIGATION KEYMAPS
    =====================================================================
    Defined in: lua/plugins/follow-md-links.lua (due to plugin load order)

    Active in markdown files:
      <CR> (Enter) - Follow markdown link (works anywhere on the link)
    =====================================================================
--]]

-- =====================
-- Autocmd definitions
-- =====================

-- Visual line mappings for markdown files
local markdown_visual_line_mappings = {
	-- Movement on display lines
	{ "n", "j", "gj" },
	{ "n", "k", "gk" },
	{ "n", "0", "g0" },
	{ "n", "$", "g$" },
	{ "n", "^", "g^" },
	{ "v", "j", "gj" },
	{ "v", "k", "gk" },
	{ "v", "0", "g0" },
	{ "v", "$", "g$" },
	{ "v", "^", "g^" },
	-- Make A, I, D work on visual lines
	{ "n", "A", "g$a" },
	{ "n", "I", "g^i" },
	{ "n", "D", "vg$hd" },
}

local autocmd_definitions = {
	terminal_window_nav = {
		event = "TermOpen",
		desc = "Set window navigation keymaps for terminal buffers",
		callback = function()
			for _, mapping in ipairs(snacks_terminal_navigation) do
				local mode, lhs, rhs, opts = mapping[1], mapping[2], mapping[3], mapping[4]
				vim.keymap.set(mode, lhs, rhs, vim.tbl_extend("force", opts, { buffer = true }))
			end
		end,
	},
	oil_disable_noice = {
		event = "FileType",
		pattern = "oil",
		desc = "Disable Noice cmdline in Oil buffers",
		callback = function()
			vim.b.noice_cmdline_disabled = true
		end,
	},
	markdown_visual_lines = {
		event = "FileType",
		pattern = { "markdown", "text" },
		desc = "Set visual line mappings for markdown/text files",
		callback = function()
			local opts = { buffer = true, noremap = true, silent = true }
			for _, mapping in ipairs(markdown_visual_line_mappings) do
				local mode, lhs, rhs = mapping[1], mapping[2], mapping[3]
				vim.keymap.set(mode, lhs, rhs, opts)
			end
		end,
	},
	conflict_marker_keymaps = {
		event = "User",
		pattern = "ConflictMarkerSetup",
		desc = "Set conflict marker keymaps for conflicted buffers",
		callback = function()
			for _, mapping in ipairs(conflict_marker_mappings) do
				local mode, lhs, rhs, opts = mapping[1], mapping[2], mapping[3], mapping[4]
				vim.keymap.set(mode, lhs, rhs, vim.tbl_extend("force", opts, { buffer = true }))
			end
		end,
	},
}

-- =====================
-- Helper functions
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

local function set_autocmd(autocmd)
	vim.api.nvim_create_autocmd(autocmd.event, {
		pattern = autocmd.pattern,
		callback = autocmd.callback,
		desc = autocmd.desc,
	})
end

-- =====================
-- Apply all keymaps and autocmds
-- =====================

-- List of all keymap groups to apply
local all_keymaps = {
	autopairs_mappings,
	basic_mappings,
	buffer_mappings,
	claudecode_mappings,
	dadbod_mappings,
	dbt_mappings,
	delete_to_blackhole_mappings,
	diagnostic_mappings,
	fastedit_mappings,
	fastnav_mappings,
	find_replace_mappings,
	flash_mappings,
	format_mappings,
	hardtime_mappings,
	harpoon_mappings,
	lazygit_mappings,
	mini_splitjoin_mappings,
	multicursor_mappings,
	noice_mappings,
	oil_mappings,
	path_yank_mappings,
	print_mappings,
	selectall_mappings,
	snacks_terminal_mappings,
	telescope_mappings,
	trouble_mappings,
	undotree_mappings,
	window_navigation_mappings,
	window_operations_mappings,
	working_dir_mappings,
	yanky_mappings,
	yazi_mappings,
}

-- List of all autocmds to apply (reference by key name)
local all_autocmds = {
	"terminal_window_nav",
	"oil_disable_noice",
	"markdown_visual_lines",
	"conflict_marker_keymaps",
}

-- Apply loops
for _, mapping_group in ipairs(all_keymaps) do
	set_keymaps(mapping_group)
end

for _, autocmd_name in ipairs(all_autocmds) do
	set_autocmd(autocmd_definitions[autocmd_name])
end

return M
