return {
	"gbprod/yanky.nvim",
	dependencies = {
		{ "kkharji/sqlite.lua" },
	},
	opts = {
		ring = {
			history_length = 100,
			storage = "shada",
			sync_with_numbered_registers = true,
			cancel_event = "update",
			ignore_registers = { "_" },
			update_register_on_cycle = false,
		},
		system_clipboard = {
			sync_with_ring = true,
			clipboard_register = nil,
		},
		picker = {
			select = {
				action = nil,
			},
			telescope = {
				use_default_mappings = true,
				mappings = nil,
			},
		},
		highlight = {
			on_put = true,
			on_yank = true,
			timer = 500,
		},
		preserve_cursor_position = {
			enabled = true,
		},
	},
}