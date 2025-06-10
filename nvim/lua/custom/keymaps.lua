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
		{ "<leader>f", group = "[F]lash", mode = { "n", "v" } },
		{ "<leader>g", group = "[G]it", mode = { "n", "v" } },
		{ "<leader>e", group = "[E]xplore", mode = { "n", "v" } },
		{ "<leader>q", group = "[Q]uickfix", mode = { "n", "v" } },
		{ "<leader>s", group = "[S]earch", mode = { "n", "v" } },
		{ "<leader>s/", group = "[S]earch [/] within files", mode = { "n", "v" } },
		{ "<leader>t", group = "[T]erminal", mode = { "n", "v" } },
		{ "<leader>t/", group = "[T]erminal [/] management", mode = { "n", "v" } },
		{ "<leader>=", group = "[=] Apply format", mode = { "n" } },
		{ "<leader>-", group = "Window splits [|]", mode = { "n", "v" } },
	})
end

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
			vim.cmd("ClaudeCode --continue")
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
			require("snacks").lazygit({ cwd = vim.loop.cwd() })
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

-- Snacks.nvim explorer (replacing neo-tree)
local snacks_explorer_mappings = {
	{
		"n",
		"<leader>ee",
		function()
			local ok, snacks = pcall(require, "snacks")
			if ok then
				snacks.explorer()
			end
		end,
		{ desc = "Toggle [EE]xplorer" },
	},
	{
		"n",
		"<leader>er",
		function()
			local ok, snacks = pcall(require, "snacks")
			if ok then
				snacks.explorer({ path = vim.fn.expand("%:p:h") })
			end
		end,
		{ desc = "[E]xplorer [R]eveal file" },
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
		{ desc = "[F]lash [F]ast navigation" },
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
	{ "n", "<leader>%", "ggVG", { noremap = true, desc = "[%] Select entire buffer" } },
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

-- Window navigation using Alt+Shift+hjkl
local window_navigation_mappings = {
	{ "n", "<A-h>", "<C-w>h", { desc = "Go to left window" } },
	{ "n", "<A-j>", "<C-w>j", { desc = "Go to lower window" } },
	{ "n", "<A-k>", "<C-w>k", { desc = "Go to upper window" } },
	{ "n", "<A-l>", "<C-w>l", { desc = "Go to right window" } },
	{ "n", "<A-n>", "<C-w>w", { desc = "Go to next window" } },
}

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
		{ desc = "[T]erminal [T]oggle" },
	},

	-- Terminal management sub-group
	{
		"n",
		"<leader>t/f",
		function()
			require("snacks.terminal").toggle()
		end,
		{ desc = "[T]erminal [/] floating" },
	},
	{
		"n",
		"<leader>t/a",
		function()
			require("snacks.terminal").toggle_all()
		end,
		{ desc = "[T]erminal [/] all terminals" },
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

-- Mini.surround keymaps
local mini_surround_mappings = {
	-- Normal and Visual mode mappings
	{
		{ "n", "v" },
		"sa",
		function()
			require("mini.surround").add()
		end,
		{ desc = "[S]urround [A]dd" },
	},
	{
		"n",
		"sd",
		function()
			require("mini.surround").delete()
		end,
		{ desc = "[S]urround [D]elete" },
	},
	{
		"n",
		"sf",
		function()
			require("mini.surround").find()
		end,
		{ desc = "[S]urround [F]ind (right)" },
	},
	{
		"n",
		"sF",
		function()
			require("mini.surround").find_left()
		end,
		{ desc = "[S]urround [F]ind (left)" },
	},
	{
		"n",
		"sh",
		function()
			require("mini.surround").highlight()
		end,
		{ desc = "[S]urround [H]ighlight" },
	},
	{
		"n",
		"sr",
		function()
			require("mini.surround").replace()
		end,
		{ desc = "[S]urround [R]eplace" },
	},
	{
		"n",
		"sn",
		function()
			require("mini.surround").update_n_lines()
		end,
		{ desc = "[S]urround update [N] lines" },
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
set_keymaps(snacks_explorer_mappings)
set_keymaps(basic_mappings)
set_keymaps(arrow_mappings)
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
set_keymaps(mini_surround_mappings)

return {}
