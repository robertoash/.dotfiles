-- ============================================================================
-- Logger Utilities
-- ============================================================================
-- Centralized logging setup and utilities
-- ============================================================================

Logger = Logger or {}

-- Create a new logger with consistent formatting
function Logger.new(name, level)
    level = level or "info"
    local logger = hs.logger.new(name, level)
    return logger
end

-- Global logger for general use
Logger.default = Logger.new("hammerspoon", "info")

-- Log helpers
function Logger.info(message)
    Logger.default.i(message)
end

function Logger.warn(message)
    Logger.default.w(message)
end

function Logger.error(message)
    Logger.default.e(message)
end

function Logger.debug(message)
    Logger.default.d(message)
end

return Logger
