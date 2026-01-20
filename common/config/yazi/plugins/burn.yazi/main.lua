--- Burn ISO to USB device plugin for Yazi

local toggle_ui = ya.sync(function(self)
	if self.children then
		Modal:children_remove(self.children)
		self.children = nil
	else
		self.children = Modal:children_add(self, 10)
	end
	ui.render()
end)

local update_devices = ya.sync(function(self, devices)
	self.devices = devices
	self.cursor = math.max(0, math.min(self.cursor or 0, #self.devices - 1))
	ui.render()
end)

local update_cursor = ya.sync(function(self, cursor)
	if #self.devices == 0 then
		self.cursor = 0
	else
		self.cursor = ya.clamp(0, self.cursor + cursor, #self.devices - 1)
	end
	ui.render()
end)

local active_device = ya.sync(function(self)
	return self.devices[self.cursor + 1]
end)

local get_hovered_file = ya.sync(function()
	local file = cx.active.current.hovered
	if file then
		return tostring(file.url)
	end
	return nil
end)

local set_iso_path = ya.sync(function(self, path)
	self.iso_path = path
end)

local get_iso_path = ya.sync(function(self)
	return self.iso_path
end)

local show_notify = ya.sync(function(self, title, content, level)
	ya.notify {
		title = title,
		content = content,
		timeout = 5,
		level = level
	}
end)

local M = {
	keys = {
		{ on = "q", run = "quit" },
		{ on = "<Esc>", run = "quit" },
		{ on = "<Enter>", run = "burn" },
		{ on = "b", run = "burn" },
		{ on = "k", run = "up" },
		{ on = "j", run = "down" },
		{ on = "<Up>", run = "up" },
		{ on = "<Down>", run = "down" },
	},
}

function M:new(area)
	self:layout(area)
	return self
end

function M:layout(area)
	local chunks = ui.Layout()
		:constraints({
			ui.Constraint.Percentage(10),
			ui.Constraint.Percentage(80),
			ui.Constraint.Percentage(10),
		})
		:split(area)

	local chunks = ui.Layout()
		:direction(ui.Layout.HORIZONTAL)
		:constraints({
			ui.Constraint.Percentage(10),
			ui.Constraint.Percentage(80),
			ui.Constraint.Percentage(10),
		})
		:split(chunks[2])

	self._area = chunks[2]
end

function M:entry(job)
	-- Get hovered file using ya.sync wrapper
	local file_path = get_hovered_file()

	if not file_path or not file_path:match("%.iso$") then
		ya.notify {
			title = "Burn ISO",
			content = "Please select an ISO file first",
			timeout = 3,
			level = "warn"
		}
		return
	end

	set_iso_path(file_path)

	toggle_ui()
	update_devices(self.obtain_usb_devices())

	local tx, rx = ya.chan("mpsc")

	function producer()
		while true do
			local cand = self.keys[ya.which { cands = self.keys, silent = true }] or { run = {} }
			local run = type(cand.run) == "table" and cand.run[1] or cand.run
			tx:send(run)
			if run == "quit" then
				toggle_ui()
				return
			end
			if run == "burn" then
				-- Exit producer loop, consumer will handle UI cleanup
				return
			end
		end
	end

	function consumer()
		repeat
			local run = rx:recv()
			if run == "quit" then
				break
			elseif run == "up" then
				update_cursor(-1)
			elseif run == "down" then
				update_cursor(1)
			elseif run == "burn" then
				local dev = active_device()
				local iso = get_iso_path()
				if dev and iso then
					-- Close UI first
					toggle_ui()

					-- Get just the filename for display
					local iso_name = iso:match("([^/]+)$") or iso
					local status_file = "/tmp/yazi_burn_status_" .. os.time()

					local cmd = string.format(
						"trap 'exit 0' INT; echo '⚠️  BURN ISO TO USB' && echo '' && echo 'Source: %s' && echo 'Target: %s (%s)' && echo '' && echo 'WARNING: All data on %s will be destroyed!' && echo '' && echo 'Burn will begin immediately after sudo password is entered.' && echo 'Press Enter to continue or Ctrl+C to cancel...' && read && sudo -k -- sh -c 'pv \"%s\" | dd of=%s bs=4M oflag=sync && sync' && echo success > %s && notify-send 'Burn Complete' 'ISO burned to %s' || echo failed > %s",
						iso_name,
						dev.name,
						dev.model or "USB",
						dev.name,
						iso,
						dev.name,
						status_file,
						dev.name,
						status_file
					)

					ya.emit("shell", { cmd, block = true, confirm = false })

					-- Check result
					local f = io.open(status_file, "r")
					if f then
						local status = f:read("*a"):gsub("%s+", "")
						f:close()
						os.remove(status_file)
						if status == "success" then
							show_notify("Burn ISO", string.format("Successfully burned to %s", dev.name), "info")
						else
							show_notify("Burn Failed", string.format("Failed to burn to %s", dev.name), "error")
						end
					else
						show_notify("Burn Cancelled", "Operation cancelled by user", "warn")
					end
					break
				else
					ya.notify {
						title = "Burn",
						content = "No device selected",
						timeout = 2,
						level = "warn"
					}
				end
			end
		until not run
	end

	ya.join(producer, consumer)
end

function M:reflow()
	return { self }
end

function M:redraw()
	local rows = {}
	for _, d in ipairs(self.devices or {}) do
		rows[#rows + 1] = ui.Row { d.name, d.size or "", d.model or "" }
	end

	if #rows == 0 then
		rows[#rows + 1] = ui.Row { "No USB devices found", "", "" }
	end

	return {
		ui.Clear(self._area),
		ui.Border(ui.Edge.ALL)
			:area(self._area)
			:type(ui.Border.ROUNDED)
			:style(ui.Style():fg("yellow"))
			:title(ui.Line("Burn ISO to USB"):align(ui.Align.CENTER)),
		ui.Table(rows)
			:area(self._area:pad(ui.Pad(1, 2, 1, 2)))
			:header(ui.Row({ "Device", "Size", "Model" }):style(ui.Style():bold()))
			:row(self.cursor)
			:row_style(ui.Style():fg("yellow"):underline())
			:widths {
				ui.Constraint.Length(15),
				ui.Constraint.Length(10),
				ui.Constraint.Percentage(70),
			},
	}
end

function M.obtain_usb_devices()
	local devices = {}

	local output, err = Command("lsblk")
		:arg({ "-d", "-o", "NAME,SIZE,TRAN,MODEL", "-J" })
		:output()

	if err then
		return devices
	end

	local data = ya.json_decode(output and output.stdout or "")
	if not data or not data.blockdevices then
		return devices
	end

	for _, dev in ipairs(data.blockdevices) do
		if dev.tran == "usb" then
			devices[#devices + 1] = {
				name = "/dev/" .. dev.name,
				size = dev.size,
				model = dev.model,
			}
		end
	end

	return devices
end

function M:click() end
function M:scroll() end
function M:touch() end

return M
