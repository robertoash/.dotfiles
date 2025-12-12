-- ============================================================================
-- App Launcher Module
-- ============================================================================
-- Application launching and shortcuts
-- Migrated from: skhd
-- ============================================================================

AppLauncher = AppLauncher or {}

local log = hs.logger.new("app-launcher", "info")

-- ============================================================================
-- WezTerm Launcher
-- ============================================================================

-- Launch WezTerm at specific directory
function AppLauncher.launch_wezterm()
	local target_dir = os.getenv("HOME") .. "/.dotfiles"
	local wezterm_bin = "/Applications/WezTerm.app"

	log.f("Launching WezTerm at %s", target_dir)

	-- CRITICAL: Must use /usr/bin/open to spawn via launchd (not as Hammerspoon child)
	--
	-- Why this approach:
	-- 1. Processes spawned by Hammerspoon inherit AXEnhancedUserInterface attribute
	-- 2. This causes windows to behave weirdly (focus-follows-mouse doesn't work)
	-- 3. They also get killed when Hammerspoon reloads (task reference lost)
	--
	-- Solution: Use /usr/bin/open to delegate spawning to launchd
	-- - launchd becomes the parent process (not Hammerspoon)
	-- - No AXEnhancedUserInterface inheritance
	-- - Process survives Hammerspoon reload
	--
	-- Note: We must call the binary directly with -a, not the .app bundle with --args
	-- because WezTerm is a CLI tool installed via Nix, not a standard .app
	--
	-- The -n flag creates a new instance even if one is running
	-- We background with & to prevent blocking Hammerspoon
	local cmd = string.format(
		"/usr/bin/open -n -a '%s' --args start --always-new-process --cwd '%s' &",
		wezterm_bin,
		target_dir
	)

	-- Use hs.execute (non-blocking) instead of os.execute (blocking)
	local success, output, error = hs.execute(cmd)
	if success then
		log.i("WezTerm launched via launchd (fully detached)")
	else
		log.e(string.format("WezTerm launch failed: %s", error or "unknown error"))
	end

	-- Tag the newly launched window as HS-launched
	-- This ensures it gets tiled even if it doesn't pass normal is_tileable() checks
	hs.timer.doAfter(0.5, function()
		-- Find the newest WezTerm window (most recently created)
		local all_windows = hs.window.allWindows()
		local newest_wezterm = nil
		local newest_id = 0

		for _, win in ipairs(all_windows) do
			local app = win:application()
			if app and app:name() == "WezTerm" then
				local win_id = win:id()
				-- Check if this window is already tagged
				if not WindowManagement.hs_launched_windows[win_id] and win_id > newest_id then
					newest_wezterm = win
					newest_id = win_id
				end
			end
		end

		if newest_wezterm and WindowManagement then
			-- Tag this window as HS-launched
			local win_id = newest_wezterm:id()
			WindowManagement.hs_launched_windows[win_id] = true
			log.i(string.format("🏷️  Tagged HS-launched window: %s (ID: %d)",
				newest_wezterm:title() or "unknown", win_id))
		end
	end)

	-- Manual retile after delay to ensure window gets tiled
	-- WezTerm needs time to fully spawn and become tileable
	hs.timer.doAfter(0.3, function()
		if WindowManagement then
			WindowManagement.tile_all_screens()
			log.i("Manually retiled after WezTerm launch")
		end
	end)
end

log.i("App launcher module loaded")

return AppLauncher
