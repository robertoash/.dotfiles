return {
	"jake-stewart/multicursor.nvim",
	branch = "1.0",
	config = function()
		local mc = require("multicursor-nvim")
		mc.setup({
			updatetime = 10,  -- More responsive real-time updates
		})

		-- Cursor customization
		local hl = vim.api.nvim_set_hl
		hl(0, "MultiCursorCursor", { reverse = true })
		hl(0, "MultiCursorVisual", { link = "Visual" })
		hl(0, "MultiCursorSign", { link = "SignColumn" })
		hl(0, "MultiCursorMatchPreview", { link = "Search" })
		hl(0, "MultiCursorDisabledCursor", { reverse = true })
		hl(0, "MultiCursorDisabledVisual", { link = "Visual" })
		hl(0, "MultiCursorDisabledSign", { link = "SignColumn" })

		-- NOTE: Global keymaps are defined in lua/custom/keymaps.lua
		
		-- Show persistent multicursor help notification
		local function show_multicursor_notif()
			vim.notify([[
🎯 Multicursor Mode Active
j/k        - Add cursor down/up
J/K        - Skip cursor down/up  
Ctrl+j/k   - Add 5 cursors down/up
n/N        - Match add cursor next/prev
s/S        - Skip match next/prev
t          - Toggle cursor
←/→        - Navigate cursors
ESC        - Exit multicursor mode]], 
				vim.log.levels.INFO, 
				{ 
					title = "Multicursor Commands",
					timeout = false,  -- Keep it persistent
					keep = function() return true end,  -- Keep it visible
				}
			)
		end
		
		-- Clear the persistent notification using Noice
		local function clear_multicursor_notif()
			vim.cmd("Noice dismiss")
		end

		-- Layer-specific keymaps (only active when cursors are active) are defined here
		mc.addKeymapLayer(function(layerSet)
			-- Show notification when entering multicursor mode
			show_multicursor_notif()
			
			-- Basic cursor line operations
			layerSet({ "n", "x" }, "j", function() mc.lineAddCursor(1) end)
			layerSet({ "n", "x" }, "k", function() mc.lineAddCursor(-1) end)
			layerSet({ "n", "x" }, "J", function() mc.lineSkipCursor(1) end)
			layerSet({ "n", "x" }, "K", function() mc.lineSkipCursor(-1) end)
			
			-- Add 5 cursors at once
			layerSet({ "n", "x" }, "<c-j>", function()
				for i = 1, 5 do
					mc.lineAddCursor(1)
				end
			end)
			layerSet({ "n", "x" }, "<c-k>", function()
				for i = 1, 5 do
					mc.lineAddCursor(-1)
				end
			end)
			
			-- Match operations
			layerSet({ "n", "x" }, "n", function() mc.matchAddCursor(1) end)
			layerSet({ "n", "x" }, "N", function() mc.matchAddCursor(-1) end)
			layerSet({ "n", "x" }, "s", function() mc.matchSkipCursor(1) end)
			layerSet({ "n", "x" }, "S", function() mc.matchSkipCursor(-1) end)

			-- Toggle cursor
			layerSet({ "n", "x" }, "t", mc.toggleCursor)

			-- Select a different cursor as the main one
			layerSet({ "n", "x" }, "<left>", mc.prevCursor)
			layerSet({ "n", "x" }, "<right>", mc.nextCursor)

			-- Enable and clear cursors using escape
			layerSet("n", "<esc>", function()
				clear_multicursor_notif()  -- Clear notification when exiting
				if not mc.cursorsEnabled() then
					mc.enableCursors()
				else
					mc.clearCursors()
				end
			end)
		end)
	end,
}