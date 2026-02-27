use std::collections::HashMap;
use std::path::Path;
use std::process::Command;

pub fn is_running() -> bool {
    Command::new("systemctl")
        .args(["is-active", "--quiet", "auditd"])
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

pub fn get_counts() -> HashMap<String, usize> {
    let mut counts = HashMap::new();

    if !has_ausearch() || !is_running() {
        return counts;
    }

    let output = match Command::new("sudo").args(["ausearch", "-k", "trycli", "--raw"]).output() {
        Ok(o) => o,
        Err(_) => return counts,
    };

    for line in String::from_utf8_lossy(&output.stdout).lines() {
        if !line.starts_with("type=SYSCALL") || !line.contains("exe=") {
            continue;
        }
        for token in line.split_whitespace() {
            if let Some(exe) = token.strip_prefix("exe=") {
                let name = Path::new(exe.trim_matches('"'))
                    .file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("")
                    .to_string();
                if !name.is_empty() {
                    *counts.entry(name).or_insert(0) += 1;
                }
                break;
            }
        }
    }
    counts
}

fn has_ausearch() -> bool {
    std::env::var("PATH")
        .unwrap_or_default()
        .split(':')
        .any(|d| Path::new(d).join("ausearch").is_file())
}

pub fn install_hint() -> &'static str {
    if cfg!(target_os = "macos") {
        "auditd not running. Enable:\n  sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.auditd.plist"
    } else {
        "auditd not running. Fix:\n  Run ~/.dotfiles/setup.py  (installs and enables auditd automatically)\n  Or manually: sudo pacman -S audit && sudo systemctl enable --now auditd"
    }
}
