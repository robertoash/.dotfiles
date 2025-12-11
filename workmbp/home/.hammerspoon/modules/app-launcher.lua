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
