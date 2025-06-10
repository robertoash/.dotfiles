return {
	{
		"nvim-telescope/telescope.nvim",
		event = "VimEnter",
		dependencies = {
			"nvim-lua/plenary.nvim",
			{
				"nvim-telescope/telescope-fzf-native.nvim",
				build = "make",
				cond = function()
					return vim.fn.executable("make") == 1
				end,
			},
			{ "nvim-telescope/telescope-ui-select.nvim" },
			{ "nvim-tree/nvim-web-devicons", enabled = vim.g.have_nerd_font },
		},
		config = function()
			-- All keymaps are now managed in custom/keymaps.lua
			-- Build ignore patterns dynamically from ~/.config/ignore/ignore
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

			local fb_actions = require("telescope._extensions.file_browser.actions")
			local actions = require("telescope.actions")

			require("telescope").setup({
				defaults = {
					file_ignore_patterns = ignore_patterns,
					hidden = true, -- Show hidden files by default
					vimgrep_arguments = {
						"rg",
						"--color=never",
						"--no-heading",
						"--with-filename",
						"--line-number",
						"--column",
						"--smart-case",
						"--hidden",
						"--glob",
						"!.git/*",
					},
				},
				pickers = {
					find_files = {
						hidden = true,
						follow = true,
					},
				},
				extensions = {
					["ui-select"] = {
						require("telescope.themes").get_dropdown(),
					},
					file_browser = {
						hijack_netrw = true,
						grouped = true,
						hidden = true,
						hide_parent_dir = true,
						mappings = {
							["i"] = {
								["<A-c>"] = fb_actions.create,
								["<S-CR>"] = fb_actions.create_from_prompt,
								["<A-r>"] = fb_actions.rename,
								["<A-m>"] = fb_actions.move,
								["<A-y>"] = fb_actions.copy,
								["<A-d>"] = fb_actions.remove,
								["<C-o>"] = fb_actions.open,
								["<C-g>"] = fb_actions.goto_parent_dir,
								["<C-e>"] = fb_actions.goto_home_dir,
								["<C-w>"] = fb_actions.goto_cwd,
								["<C-t>"] = fb_actions.change_cwd,
								["<C-f>"] = fb_actions.toggle_browser,
								["<C-s>"] = fb_actions.toggle_all,
								["<bs>"] = fb_actions.backspace,
								["<C-h>"] = fb_actions.goto_parent_dir,
								["<C-j>"] = actions.move_selection_better,
								["<C-k>"] = actions.move_selection_worse,
								["<C-l>"] = actions.select_default,
							},
							["n"] = {
								["c"] = fb_actions.create,
								["r"] = fb_actions.rename,
								["m"] = fb_actions.move,
								["y"] = fb_actions.copy,
								["d"] = fb_actions.remove,
								["o"] = fb_actions.open,
								["g"] = fb_actions.goto_parent_dir,
								["e"] = fb_actions.goto_home_dir,
								["w"] = fb_actions.goto_cwd,
								["t"] = fb_actions.change_cwd,
								["f"] = fb_actions.toggle_browser,
								["s"] = fb_actions.toggle_all,
								["h"] = fb_actions.goto_parent_dir,
								["j"] = actions.move_selection_better,
								["k"] = actions.move_selection_worse,
								["l"] = actions.select_default,
							},
						},
					},
				},
			})

			-- Enable Telescope extensions if they are installed
			pcall(require("telescope").load_extension, "fzf")
			pcall(require("telescope").load_extension, "ui-select")

			-- All keymaps are now managed in custom/keymaps.lua
		end,
	},

	-- Telescope extensions
	{
		"nvim-telescope/telescope-file-browser.nvim",
		dependencies = { "nvim-telescope/telescope.nvim", "nvim-lua/plenary.nvim" },
		config = function()
			require("telescope").load_extension("file_browser")
			-- All keymaps are now managed in custom/keymaps.lua
		end,
	},

	{
		"nvim-telescope/telescope-frecency.nvim",
		version = "*",
		config = function()
			require("telescope").load_extension("frecency")
			-- All keymaps are now managed in custom/keymaps.lua
		end,
	},
}