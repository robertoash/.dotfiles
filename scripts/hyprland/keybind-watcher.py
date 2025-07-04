#!/usr/bin/env python3
"""
Hyprland Keybind File Watcher
Monitors /tmp/active_keyboard_layout and source keybinds for changes
Automatically regenerates active keybinds when layout changes
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    print("ERROR: watchdog package is required. Install with: pip install watchdog")
    sys.exit(1)

# Configuration
LAYOUT_FILE = Path("/tmp/active_keyboard_layout")
SOURCE_CONFIG = Path.home() / ".config" / "hypr" / "keybinds_source.conf"
TARGET_CONFIG = Path.home() / ".config" / "hypr" / "active_keybinds.conf"
TRANSLATE_SCRIPT = Path.home() / ".config" / "scripts" / "hyprland" / "translate-keybinds.py"
PIDFILE = Path("/tmp/keybind-watcher.pid")
LOGFILE = Path("/tmp/keybind-watcher.log")


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[34m',     # Blue
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET if color else ''
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


class KeybindWatcher:
    """Main keybind watcher class"""
    
    def __init__(self):
        self.setup_logging()
        self.observer = Observer()
        self.running = False
        
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logger
        self.logger = logging.getLogger('keybind-watcher')
        self.logger.setLevel(logging.INFO)
        
        # Create formatters
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        try:
            file_handler = logging.FileHandler(LOGFILE)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"Could not create log file: {e}")
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        missing_deps = []
        
        if not TRANSLATE_SCRIPT.exists():
            self.logger.error(f"Translation script not found: {TRANSLATE_SCRIPT}")
            return False
            
        if not TRANSLATE_SCRIPT.is_file() or not os.access(TRANSLATE_SCRIPT, os.X_OK):
            self.logger.error(f"Translation script is not executable: {TRANSLATE_SCRIPT}")
            return False
            
        return True
    
    def ensure_layout_file(self):
        """Create initial layout file if it doesn't exist"""
        if not LAYOUT_FILE.exists():
            self.logger.warning("Layout file not found, creating with default 'swedish'")
            try:
                LAYOUT_FILE.write_text("swedish\n")
            except Exception as e:
                self.logger.error(f"Failed to create layout file: {e}")
                return False
        return True
    
    def run_translation(self, force: bool = False) -> bool:
        """Run the translation script"""
        try:
            cmd = ["python", str(TRANSLATE_SCRIPT)]
            if force:
                cmd.append("--force")
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("Translation completed successfully")
                return True
            else:
                self.logger.error(f"Translation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Translation script timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to run translation: {e}")
            return False
    
    def get_current_layout(self) -> str:
        """Get current layout from file"""
        try:
            if LAYOUT_FILE.exists():
                return LAYOUT_FILE.read_text().strip()
            return "swedish"
        except Exception as e:
            self.logger.error(f"Failed to read layout file: {e}")
            return "swedish"
    
    def check_existing_instance(self) -> bool:
        """Check if another instance is already running"""
        if PIDFILE.exists():
            try:
                existing_pid = int(PIDFILE.read_text().strip())
                
                # Check if process is still running
                try:
                    os.kill(existing_pid, 0)
                    self.logger.error(f"Another instance is already running (PID: {existing_pid})")
                    return False
                except OSError:
                    self.logger.warning("Stale PID file found, removing")
                    PIDFILE.unlink()
                    
            except (ValueError, OSError) as e:
                self.logger.warning(f"Invalid PID file, removing: {e}")
                PIDFILE.unlink()
                
        return True
    
    def write_pid(self):
        """Write current PID to file"""
        try:
            PIDFILE.write_text(str(os.getpid()))
        except Exception as e:
            self.logger.error(f"Failed to write PID file: {e}")
    
    def cleanup(self):
        """Cleanup on exit"""
        self.logger.info("Cleaning up keybind watcher...")
        
        if PIDFILE.exists():
            try:
                PIDFILE.unlink()
            except Exception as e:
                self.logger.warning(f"Failed to remove PID file: {e}")
        
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        
        self.logger.info("Keybind watcher stopped")


class LayoutFileHandler(FileSystemEventHandler):
    """Handler for layout file changes"""
    
    def __init__(self, watcher: KeybindWatcher):
        self.watcher = watcher
        self.last_layout = watcher.get_current_layout()
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if Path(event.src_path) == LAYOUT_FILE:
            # Small delay to ensure file is fully written
            time.sleep(0.1)
            
            current_layout = self.watcher.get_current_layout()
            
            if current_layout != self.last_layout:
                self.watcher.logger.info(f"Layout changed from {self.last_layout} to {current_layout}")
                self.last_layout = current_layout
                
                if self.watcher.run_translation():
                    self.watcher.logger.info(f"Keybinds translated successfully for layout: {current_layout}")
                else:
                    self.watcher.logger.error(f"Failed to translate keybinds for layout: {current_layout}")


class SourceConfigHandler(FileSystemEventHandler):
    """Handler for source config file changes"""
    
    def __init__(self, watcher: KeybindWatcher):
        self.watcher = watcher
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if Path(event.src_path) == SOURCE_CONFIG:
            self.watcher.logger.info("Source config file changed")
            
            # Small delay to ensure file is fully written
            time.sleep(0.1)
            
            if self.watcher.run_translation(force=True):
                self.watcher.logger.info("Keybinds retranslated after source config change")
            else:
                self.watcher.logger.error("Failed to retranslate keybinds after source config change")


def start_daemon():
    """Start the keybind watcher daemon"""
    watcher = KeybindWatcher()
    
    # Check if another instance is running
    if not watcher.check_existing_instance():
        return 1
    
    # Check dependencies
    if not watcher.check_dependencies():
        return 1
    
    # Ensure layout file exists
    if not watcher.ensure_layout_file():
        return 1
    
    # Write PID file
    watcher.write_pid()
    
    try:
        # Run initial translation
        watcher.logger.info("Starting keybind watcher daemon...")
        watcher.logger.info("Running initial keybind translation...")
        
        if not watcher.run_translation(force=True):
            watcher.logger.error("Initial translation failed")
            return 1
        
        # Setup file watchers
        layout_handler = LayoutFileHandler(watcher)
        source_handler = SourceConfigHandler(watcher)
        
        # Watch layout file directory
        layout_dir = LAYOUT_FILE.parent
        watcher.observer.schedule(layout_handler, str(layout_dir), recursive=False)
        
        # Watch source config directory
        source_dir = SOURCE_CONFIG.parent
        watcher.observer.schedule(source_handler, str(source_dir), recursive=False)
        
        # Start observer
        watcher.observer.start()
        watcher.running = True
        
        watcher.logger.info(f"Monitoring layout file: {LAYOUT_FILE}")
        watcher.logger.info(f"Monitoring source config: {SOURCE_CONFIG}")
        watcher.logger.info("Keybind watcher started successfully")
        
        # Keep daemon running
        try:
            while watcher.running:
                time.sleep(1)
        except KeyboardInterrupt:
            watcher.logger.info("Received interrupt signal")
            
    except Exception as e:
        watcher.logger.error(f"Daemon failed: {e}")
        return 1
    finally:
        watcher.cleanup()
        
    return 0


def stop_daemon():
    """Stop the keybind watcher daemon"""
    if not PIDFILE.exists():
        print("No PID file found, daemon may not be running")
        return 1
    
    try:
        pid = int(PIDFILE.read_text().strip())
        
        # Check if process is running
        try:
            os.kill(pid, 0)
        except OSError:
            print("PID file exists but process is not running")
            PIDFILE.unlink()
            return 1
        
        # Send termination signal
        print(f"Stopping keybind watcher (PID: {pid})")
        os.kill(pid, 15)  # SIGTERM
        
        # Wait for process to die
        for i in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except OSError:
                break
        else:
            print("Process didn't stop gracefully, forcing termination")
            os.kill(pid, 9)  # SIGKILL
        
        # Clean up PID file
        if PIDFILE.exists():
            PIDFILE.unlink()
        
        print("Keybind watcher stopped")
        return 0
        
    except (ValueError, OSError) as e:
        print(f"Failed to stop daemon: {e}")
        return 1


def show_status():
    """Show daemon status"""
    print("Keybind Watcher Status")
    print("=" * 22)
    print(f"Layout file: {LAYOUT_FILE}")
    print(f"Source config: {SOURCE_CONFIG}")
    print(f"Target config: {TARGET_CONFIG}")
    print(f"Translation script: {TRANSLATE_SCRIPT}")
    print(f"PID file: {PIDFILE}")
    print(f"Log file: {LOGFILE}")
    print()
    
    # Check daemon status
    if PIDFILE.exists():
        try:
            pid = int(PIDFILE.read_text().strip())
            try:
                os.kill(pid, 0)
                print(f"Status: Running (PID: {pid})")
            except OSError:
                print("Status: Not running (stale PID file)")
        except ValueError:
            print("Status: Not running (invalid PID file)")
    else:
        print("Status: Not running")
    
    print()
    
    # Show current layout
    if LAYOUT_FILE.exists():
        try:
            current_layout = LAYOUT_FILE.read_text().strip()
            print(f"Current layout: {current_layout}")
        except Exception as e:
            print(f"Current layout: Error reading file ({e})")
    else:
        print("Current layout: Not set")
    
    print()
    
    # Show recent log entries
    if LOGFILE.exists():
        try:
            lines = LOGFILE.read_text().splitlines()
            print("Recent log entries:")
            for line in lines[-5:]:
                print(f"  {line}")
        except Exception as e:
            print(f"Failed to read log file: {e}")


def force_translate():
    """Force translation of keybinds"""
    watcher = KeybindWatcher()
    
    if not watcher.check_dependencies():
        return 1
    
    if watcher.run_translation(force=True):
        print("Translation completed successfully")
        return 0
    else:
        print("Translation failed")
        return 1


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Hyprland Keybind File Watcher")
    parser.add_argument("command", choices=["start", "stop", "restart", "status", "force-translate"],
                       help="Command to execute")
    
    if len(sys.argv) < 2:
        parser.print_help()
        return 1
    
    args = parser.parse_args()
    
    if args.command == "start":
        return start_daemon()
    elif args.command == "stop":
        return stop_daemon()
    elif args.command == "restart":
        stop_daemon()
        time.sleep(1)
        return start_daemon()
    elif args.command == "status":
        show_status()
        return 0
    elif args.command == "force-translate":
        return force_translate()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())