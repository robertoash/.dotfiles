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

--=============================================================================
-- AUTOCOMMANDS
--=============================================================================
-- Force tabs to spaces after guess-indent
vim.api.nvim_create_autocmd("BufReadPost", {
	callback = function()
		-- If guess-indent chose tabs, override with your own taste
		if not vim.o.expandtab then
			vim.o.expandtab = true
			vim.o.shiftwidth = 4
			vim.o.tabstop = 4
		end
	end,
})

-- Highlight when yanking (copying) text
vim.api.nvim_create_autocmd("TextYankPost", {
	desc = "Highlight when yanking (copying) text",
	group = vim.api.nvim_create_augroup("kickstart-highlight-yank", { clear = true }),
	callback = function()
		vim.hl.on_yank()
	end,
})

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
-- PLUGINS
--=============================================================================
require("lazy").setup({
	---------------------------
	-- DIRECT IMPORTS
	-- ------------------------

	{
		import = "plugins.neo-tree"
	},

	---------------------------
	-- UTILITY PLUGINS
	---------------------------
	-- Indentation detection
	"NMAC427/guess-indent.nvim",

	-- Git integration
	{
		"lewis6991/gitsigns.nvim",
		opts = {
			signs = {
				add = { text = "+" },
				change = { text = "~" },
				delete = { text = "_" },
				topdelete = { text = "‾" },
				changedelete = { text = "~" },
			},
		},
	},

	-- Keybinding helper
	{
		"folke/which-key.nvim",
		event = "VimEnter",
		opts = {
			delay = 0,
			icons = {
				mappings = vim.g.have_nerd_font,
				keys = vim.g.have_nerd_font and {} or {
					Up = "<Up> ",
					Down = "<Down> ",
					Left = "<Left> ",
					Right = "<Right> ",
					C = "<C-…> ",
					M = "<M-…> ",
					D = "<D-…> ",
					S = "<S-…> ",
					CR = "<CR> ",
					Esc = "<Esc> ",
					ScrollWheelDown = "<ScrollWheelDown> ",
					ScrollWheelUp = "<ScrollWheelUp> ",
					NL = "<NL> ",
					BS = "<BS> ",
					Space = "<Space> ",
					Tab = "<Tab> ",
					F1 = "<F1>",
					F2 = "<F2>",
					F3 = "<F3>",
					F4 = "<F4>",
					F5 = "<F5>",
					F6 = "<F6>",
					F7 = "<F7>",
					F8 = "<F8>",
					F9 = "<F9>",
					F10 = "<F10>",
					F11 = "<F11>",
					F12 = "<F12>",
				},
			},

			-- Document existing key chains
			spec = {
				{ "<leader>s", group = "[S]earch" },
				{ "<leader>t", group = "[T]oggle" },
				{ "<leader>h", group = "Git [H]unk", mode = { "n", "v" } },
			},
		},
	},

	---------------------------
	-- AI
	---------------------------

	{
		"greggh/claude-code.nvim",
		dependencies = {
			"nvim-lua/plenary.nvim", -- Required for git operations
		},
		config = function()
			require("claude-code").setup({
				-- Terminal window settings
				window = {
					split_ratio = 0.3, -- How much screen real estate to give Claude (height/width)
					position = "botright", -- Where to put the window ("botright", "topleft", etc.)
					enter_insert = true, -- Jump right into typing mode
					hide_numbers = true, -- Clean up the UI a bit
				},

				-- Auto-reload when Claude updates your files
				refresh = {
					enable = true, -- This is like magic - Claude edits a file, it updates in Neovim!
					timer_interval = 1000, -- Check for changes every second
					show_notifications = true, -- "Psst, Claude just changed something!"
				},

				-- Git settings (very handy!)
				git = {
					use_git_root = true, -- Start Claude in the project root
				},
				-- Claude-code keymaps
				-- Open Claude Code with <leader>cc
				vim.keymap.set("n", "<leader>cc", "<cmd>ClaudeCode<CR>", { desc = "Open Claude Code" }),
				-- Continue conversation with <leader>cn
				vim.keymap.set(
					"n",
					"<leader>cn",
					"<cmd>ClaudeCode --continue<CR>",
					{ desc = "Continue with Claude Code" }
				),
			})
		end,
	},

	{
		"yetone/avante.nvim",
		event = "VeryLazy",
		version = false, -- Never set this value to "*"! Never!
		opts = {
			-- add any opts here
			-- for example
			provider = "openai",
			openai = {
				endpoint = "https://api.openai.com/v1",
				model = "gpt-4o", -- your desired model (or use gpt-4o, etc.)
				timeout = 30000, -- Timeout in milliseconds, increase this for reasoning models
				temperature = 0,
				max_completion_tokens = 8192, -- Increase this to include reasoning tokens (for reasoning models)
				--reasoning_effort = "medium", -- low|medium|high, only used for reasoning models
			},
		},
		-- if you want to build from source then do `make BUILD_FROM_SOURCE=true`
		build = "make",
		-- build = "powershell -ExecutionPolicy Bypass -File Build.ps1 -BuildFromSource false" -- for windows
		dependencies = {
			"nvim-treesitter/nvim-treesitter",
			"stevearc/dressing.nvim",
			"nvim-lua/plenary.nvim",
			"MunifTanjim/nui.nvim",
			--- The below dependencies are optional,
			"echasnovski/mini.pick", -- for file_selector provider mini.pick
			"nvim-telescope/telescope.nvim", -- for file_selector provider telescope
			"hrsh7th/nvim-cmp", -- autocompletion for avante commands and mentions
			"ibhagwan/fzf-lua", -- for file_selector provider fzf
			"nvim-tree/nvim-web-devicons", -- or echasnovski/mini.icons
			"zbirenbaum/copilot.lua", -- for providers='copilot'
			{
				-- support for image pasting
				"HakonHarnes/img-clip.nvim",
				event = "VeryLazy",
				opts = {
					-- recommended settings
					default = {
						embed_image_as_base64 = false,
						prompt_for_file_name = false,
						drag_and_drop = {
							insert_mode = true,
						},
						-- required for Windows users
						use_absolute_path = true,
					},
				},
			},
			{
				-- Make sure to set this up properly if you have lazy=true
				"MeanderingProgrammer/render-markdown.nvim",
				opts = {
					file_types = { "markdown", "Avante" },
				},
				ft = { "markdown", "Avante" },
			},
		},
	},

	---------------------------
	-- TELESCOPE (FUZZY FINDER)
	---------------------------
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

			-- See `:help telescope.builtin`
			local builtin = require("telescope.builtin")
			vim.keymap.set("n", "<leader>sh", builtin.help_tags, { desc = "[S]earch [H]elp" })
			vim.keymap.set("n", "<leader>sk", builtin.keymaps, { desc = "[S]earch [K]eymaps" })
			vim.keymap.set("n", "<leader>sf", builtin.find_files, { desc = "[S]earch [F]iles" })
			vim.keymap.set("n", "<leader>ss", builtin.builtin, { desc = "[S]earch [S]elect Telescope" })
			vim.keymap.set("n", "<leader>sw", builtin.grep_string, { desc = "[S]earch current [W]ord" })
			vim.keymap.set("n", "<leader>sg", builtin.live_grep, { desc = "[S]earch by [G]rep" })
			vim.keymap.set("n", "<leader>sd", builtin.diagnostics, { desc = "[S]earch [D]iagnostics" })
			vim.keymap.set("n", "<leader>sr", builtin.resume, { desc = "[S]earch [R]esume" })
			vim.keymap.set("n", "<leader>s.", builtin.oldfiles, { desc = '[S]earch Recent Files ("." for repeat)' })
			vim.keymap.set("n", "<leader><leader>", builtin.buffers, { desc = "[ ] Find existing buffers" })

			-- Slightly advanced example of overriding default behavior and theme
			vim.keymap.set("n", "<leader>/", function()
				-- You can pass additional configuration to Telescope to change the theme, layout, etc.
				builtin.current_buffer_fuzzy_find(require("telescope.themes").get_dropdown({
					winblend = 10,
					previewer = false,
				}))
			end, { desc = "[/] Fuzzily search in current buffer" })

			-- It's also possible to pass additional configuration options.
			--  See `:help telescope.builtin.live_grep()` for information about particular keys
			vim.keymap.set("n", "<leader>s/", function()
				builtin.live_grep({
					grep_open_files = true,
					prompt_title = "Live Grep in Open Files",
				})
			end, { desc = "[S]earch [/] in Open Files" })

			-- Shortcut for searching your Neovim configuration files
			vim.keymap.set("n", "<leader>sn", function()
				builtin.find_files({ cwd = vim.fn.stdpath("config") })
			end, { desc = "[S]earch [N]eovim files" })
		end,
	},

	-- Telescope extensions
	{
		"nvim-telescope/telescope-file-browser.nvim",
		dependencies = { "nvim-telescope/telescope.nvim", "nvim-lua/plenary.nvim" },
		config = function()
			require("telescope").load_extension("file_browser")
		end,
	},
	{
		"nvim-telescope/telescope-frecency.nvim",
		version = "*",
		config = function()
			require("telescope").load_extension("frecency")
			-- Add frecency finder with custom options
			vim.keymap.set("n", "<leader>ff", function()
				require("telescope").extensions.frecency.frecency({
					hidden = true,
					no_ignore = true,
				})
			end, { desc = "[F]ind [F]recent files (including hidden & ignored)" })
		end,
	},

	---------------------------
	-- LSP PLUGINS
	---------------------------
	{
		"folke/lazydev.nvim",
		ft = "lua",
		opts = {
			library = {
				{ path = "${3rd}/luv/library", words = { "vim%.uv" } },
			},
		},
	},
	{
		"neovim/nvim-lspconfig",
		dependencies = {
			{ "mason-org/mason.nvim", opts = {} },
			"mason-org/mason-lspconfig.nvim",
			"WhoIsSethDaniel/mason-tool-installer.nvim",
			{ "j-hui/fidget.nvim", opts = {} },
			"saghen/blink.cmp",
		},
		config = function()
			vim.api.nvim_create_autocmd("LspAttach", {
				group = vim.api.nvim_create_augroup("kickstart-lsp-attach", { clear = true }),
				callback = function(event)
					local map = function(keys, func, desc, mode)
						mode = mode or "n"
						vim.keymap.set(mode, keys, func, { buffer = event.buf, desc = "LSP: " .. desc })
					end

					-- Rename the variable under your cursor.
					map("grn", vim.lsp.buf.rename, "[R]e[n]ame")

					-- Execute a code action, usually your cursor needs to be on top of an error
					-- or a suggestion from your LSP for this to activate.
					map("gra", vim.lsp.buf.code_action, "[G]oto Code [A]ction", { "n", "x" })

					-- Find references for the word under your cursor.
					map("grr", require("telescope.builtin").lsp_references, "[G]oto [R]eferences")

					-- Jump to the implementation of the word under your cursor.
					map("gri", require("telescope.builtin").lsp_implementations, "[G]oto [I]mplementation")

					-- Jump to the definition of the word under your cursor.
					map("grd", require("telescope.builtin").lsp_definitions, "[G]oto [D]efinition")

					-- Jump to the declaration of the word under your cursor.
					map("grD", vim.lsp.buf.declaration, "[G]oto [D]eclaration")

					-- Fuzzy find all the symbols in your current document.
					map("gO", require("telescope.builtin").lsp_document_symbols, "Open Document Symbols")

					-- Fuzzy find all the symbols in your current workspace.
					map("gW", require("telescope.builtin").lsp_dynamic_workspace_symbols, "Open Workspace Symbols")

					-- Jump to the type of the word under your cursor.
					map("grt", require("telescope.builtin").lsp_type_definitions, "[G]oto [T]ype Definition")

					-- This function resolves a difference between neovim nightly (version 0.11) and stable (version 0.10)
					---@param client vim.lsp.Client
					---@param method vim.lsp.protocol.Method
					---@param bufnr? integer some lsp support methods only in specific files
					---@return boolean
					local function client_supports_method(client, method, bufnr)
						if vim.fn.has("nvim-0.11") == 1 then
							return client:supports_method(method, bufnr)
						else
							return client.supports_method(method, { bufnr = bufnr })
						end
					end

					-- The following two autocommands are used to highlight references of the
					-- word under your cursor when your cursor rests there for a little while.
					local client = vim.lsp.get_client_by_id(event.data.client_id)
					if
						client
						and client_supports_method(
							client,
							vim.lsp.protocol.Methods.textDocument_documentHighlight,
							event.buf
						)
					then
						local highlight_augroup =
							vim.api.nvim_create_augroup("kickstart-lsp-highlight", { clear = false })
						vim.api.nvim_create_autocmd({ "CursorHold", "CursorHoldI" }, {
							buffer = event.buf,
							group = highlight_augroup,
							callback = vim.lsp.buf.document_highlight,
						})

						vim.api.nvim_create_autocmd({ "CursorMoved", "CursorMovedI" }, {
							buffer = event.buf,
							group = highlight_augroup,
							callback = vim.lsp.buf.clear_references,
						})

						vim.api.nvim_create_autocmd("LspDetach", {
							group = vim.api.nvim_create_augroup("kickstart-lsp-detach", { clear = true }),
							callback = function(event2)
								vim.lsp.buf.clear_references()
								vim.api.nvim_clear_autocmds({ group = "kickstart-lsp-highlight", buffer = event2.buf })
							end,
						})
					end

					-- The following code creates a keymap to toggle inlay hints in your
					-- code, if the language server you are using supports them
					if
						client
						and client_supports_method(client, vim.lsp.protocol.Methods.textDocument_inlayHint, event.buf)
					then
						map("<leader>th", function()
							vim.lsp.inlay_hint.enable(not vim.lsp.inlay_hint.is_enabled({ bufnr = event.buf }))
						end, "[T]oggle Inlay [H]ints")
					end
				end,
			})

			-- Diagnostic Config
			vim.diagnostic.config({
				severity_sort = true,
				float = { border = "rounded", source = "if_many" },
				underline = { severity = vim.diagnostic.severity.ERROR },
				signs = vim.g.have_nerd_font and {
					text = {
						[vim.diagnostic.severity.ERROR] = "󰅚 ",
						[vim.diagnostic.severity.WARN] = "󰀪 ",
						[vim.diagnostic.severity.INFO] = "󰋽 ",
						[vim.diagnostic.severity.HINT] = "󰌶 ",
					},
				} or {},
				virtual_text = {
					source = "if_many",
					spacing = 2,
					format = function(diagnostic)
						local diagnostic_message = {
							[vim.diagnostic.severity.ERROR] = diagnostic.message,
							[vim.diagnostic.severity.WARN] = diagnostic.message,
							[vim.diagnostic.severity.INFO] = diagnostic.message,
							[vim.diagnostic.severity.HINT] = diagnostic.message,
						}
						return diagnostic_message[diagnostic.severity]
					end,
				},
			})

			local capabilities = require("blink.cmp").get_lsp_capabilities()

			-- Enable the following language servers
			local servers = {
				lua_ls = {
					settings = {
						Lua = {
							completion = {
								callSnippet = "Replace",
							},
						},
					},
				},
			}

			-- Ensure the servers and tools above are installed
			local ensure_installed = vim.tbl_keys(servers or {})
			vim.list_extend(ensure_installed, {
				"stylua", -- Used to format Lua code
				"black",
				"pyright",
			})
			require("mason-tool-installer").setup({ ensure_installed = ensure_installed })

			require("mason-lspconfig").setup({
				ensure_installed = {}, -- explicitly set to an empty table (Kickstart populates installs via mason-tool-installer)
				automatic_installation = false,
				handlers = {
					function(server_name)
						local server = servers[server_name] or {}
						-- This handles overriding only values explicitly passed
						-- by the server configuration above. Useful when disabling
						-- certain features of an LSP (for example, turning off formatting for ts_ls)
						server.capabilities = vim.tbl_deep_extend("force", {}, capabilities, server.capabilities or {})
						require("lspconfig")[server_name].setup(server)
					end,
				},
			})
			-- Auto-format on save - like having a tiny robot butler tidy your code! 🤖
			vim.api.nvim_create_autocmd("BufWritePre", {
				pattern = "*.py",
				callback = function()
					vim.lsp.buf.format({ timeout_ms = 1000 })
				end,
			})
		end,
	},

	---------------------------
	-- FORMATTING AND COMPLETION
	---------------------------
	{
		"stevearc/conform.nvim",
		event = { "BufWritePre" },
		cmd = { "ConformInfo" },
		keys = {
			{
				"<leader>f",
				function()
					require("conform").format({ async = true, lsp_format = "fallback" })
				end,
				mode = "",
				desc = "[F]ormat buffer",
			},
		},
		opts = {
			notify_on_error = false,
			format_on_save = function(bufnr)
				-- Disable "format_on_save lsp_fallback" for languages that don't
				-- have a well standardized coding style. You can add additional
				-- languages here or re-enable it for the disabled ones.
				local disable_filetypes = { c = true, cpp = true }
				if disable_filetypes[vim.bo[bufnr].filetype] then
					return nil
				else
					return {
						timeout_ms = 500,
						lsp_format = "fallback",
					}
				end
			end,
			formatters_by_ft = {
				lua = { "stylua" },
			},
		},
	},

	{
		"saghen/blink.cmp",
		event = "VimEnter",
		version = "1.*",
		dependencies = {
			{
				"L3MON4D3/LuaSnip",
				version = "2.*",
				build = (function()
					if vim.fn.has("win32") == 1 or vim.fn.executable("make") == 0 then
						return
					end
					return "make install_jsregexp"
				end)(),
				dependencies = {},
				opts = {},
			},
			"folke/lazydev.nvim",
		},
		opts = {
			keymap = {
				preset = "super-tab",
			},

			appearance = {
				nerd_font_variant = "mono",
			},

			completion = {
				documentation = { auto_show = false, auto_show_delay_ms = 500 },
			},

			sources = {
				default = { "lsp", "path", "snippets", "lazydev" },
				providers = {
					lazydev = { module = "lazydev.integrations.blink", score_offset = 100 },
				},
			},

			snippets = { preset = "luasnip" },
			fuzzy = { implementation = "prefer_rust_with_warning" },
			-- fuzzy = { implementation = "lua" },
			signature = { enabled = true },
		},
	},

	---------------------------
	-- UI ENHANCEMENTS
	---------------------------
	{
		"folke/todo-comments.nvim",
		event = "VimEnter",
		dependencies = { "nvim-lua/plenary.nvim" },
		opts = { signs = false },
	},

	{
		"echasnovski/mini.nvim",
		config = function()
			-- Better Around/Inside textobjects
			require("mini.ai").setup({ n_lines = 500 })

			-- Add/delete/replace surroundings (brackets, quotes, etc.)
			require("mini.surround").setup()

			-- Simple and easy statusline.
			local statusline = require("mini.statusline")
			statusline.setup({ use_icons = vim.g.have_nerd_font })

			---@diagnostic disable-next-line: duplicate-set-field
			statusline.section_location = function()
				return "%2l:%-2v"
			end
		end,
	},

	---------------------------
	-- SYNTAX AND PARSING
	---------------------------
	{
		"nvim-treesitter/nvim-treesitter",
		build = ":TSUpdate",
		main = "nvim-treesitter.configs",
		opts = {
			ensure_installed = {
				"bash",
				"c",
				"diff",
				"html",
				"lua",
				"luadoc",
				"markdown",
				"markdown_inline",
				"python",
				"query",
				"vim",
				"vimdoc",
			},
			auto_install = true,
			highlight = {
				enable = true,
				additional_vim_regex_highlighting = { "ruby" },
			},
			indent = { enable = true, disable = { "ruby" } },
		},
	},
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
-- CUSTOM FUNCTIONS
--=============================================================================
-- :W - write with mkdir -p
vim.api.nvim_create_user_command("W", function()
	local file = vim.api.nvim_buf_get_name(0)
	local dir = vim.fn.fnamemodify(file, ":p:h")
	if vim.fn.isdirectory(dir) == 0 then
		vim.fn.mkdir(dir, "p")
	end
	vim.cmd("write")
end, {})

-- :WQ - write and quit with mkdir -p
vim.api.nvim_create_user_command("WQ", function()
	local file = vim.api.nvim_buf_get_name(0)
	local dir = vim.fn.fnamemodify(file, ":p:h")
	if vim.fn.isdirectory(dir) == 0 then
		vim.fn.mkdir(dir, "p")
	end
	vim.cmd("wq")
end, {})

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
-- KEYMAPS
--=============================================================================
-- Note: Additional plugin-specific keymaps can be found in their respective plugin configs
-- Telescope keymaps: <leader>s*, <leader>/, <leader>ff
-- LSP keymaps: gr*, gO, gW, <leader>th
-- Format keymap: <leader>f

-- Basic movement and operations
vim.keymap.set("n", "<Esc>", "<cmd>nohlsearch<CR>")
vim.keymap.set("t", "<Esc><Esc>", "<C-\\><C-n>", { desc = "Exit terminal mode" })

-- Disable arrow keys in normal mode
vim.keymap.set("n", "<left>", "<cmd>echo 'Use h to move!!'<CR>")
vim.keymap.set("n", "<right>", "<cmd>echo 'Use l to move!!'<CR>")
vim.keymap.set("n", "<up>", "<cmd>echo 'Use k to move!!'<CR>")
vim.keymap.set("n", "<down>", "<cmd>echo 'Use j to move!!'<CR>")

-- Faster navigation
vim.keymap.set("n", "<C-j>", "10j", { desc = "Move down 10 times" })
vim.keymap.set("n", "<C-k>", "10k", { desc = "Move up 10 times" })

-- Window navigation
vim.keymap.set("n", "<C-s-h>", "<C-w><C-h>", { desc = "Move focus to the left window" })
vim.keymap.set("n", "<C-s-l>", "<C-w><C-l>", { desc = "Move focus to the right window" })
vim.keymap.set("n", "<C-s-j>", "<C-w><C-j>", { desc = "Move focus to the lower window" })
vim.keymap.set("n", "<C-s-k>", "<C-w><C-k>", { desc = "Move focus to the upper window" })

-- Diagnostics
vim.keymap.set("n", "<leader>q", vim.diagnostic.setloclist, { desc = "Open diagnostic [Q]uickfix list" })

-- File Browser
vim.keymap.set("n", "<leader>sb", ":Telescope file_browser<CR>", { desc = "[S]earch with file [B]rowser" })

-- Buffer operations
vim.keymap.set("n", "<leader>bd", ":bd<CR>", { desc = "[B]uffer [D]elete" })
vim.keymap.set("n", "<leader>bp", ":bp<CR>", { desc = "[B]uffer [P]revious" })
vim.keymap.set("n", "<leader>bn", ":bn<CR>", { desc = "[B]uffer [N]ext" })

-- Select whole document
-- Map <leader>% to grab the ENTIRE document like a document-hungry kraken
vim.keymap.set("n", "<leader>%", "ggVG", { noremap = true, desc = "Select entire buffer" })

-- Reveal current file in NeoTree
vim.keymap.set('n', '<leader>e.', function()
    local reveal_file = vim.fn.expand('%:p')
    if (reveal_file == '') then
      reveal_file = vim.fn.getcwd()
    else
      local f = io.open(reveal_file, "r")
      if (f) then
        f.close(f)
      else
        reveal_file = vim.fn.getcwd()
      end
    end
    require('neo-tree.command').execute({
      action = "focus",          -- OPTIONAL, this is the default value
      source = "filesystem",     -- OPTIONAL, this is the default value
      position = "left",         -- OPTIONAL, this is the default value
      reveal_file = reveal_file, -- path to file or folder to reveal
      reveal_force_cwd = true,   -- change cwd without asking if needed
    })
    end,
    { desc = "Open neo-tree at current file or working directory" }
);
