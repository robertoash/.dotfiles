use std::collections::HashMap;
use std::path::Path;
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

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

    let since = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
        .saturating_sub(30 * 86400);

    let output = match Command::new("sudo")
        .args(["ausearch", "-k", "trycli", "--raw", "-ts", "this-month"])
        .output()
    {
        Ok(o) => o,
        Err(_) => return counts,
    };

    // ausearch --raw outputs one record per line with no "----" separators.
    // Records belonging to the same event share the same serial number in
    // msg=audit(TIMESTAMP:SERIAL). We group by serial to detect event boundaries.
    // We only count interactive (tty=pts) executions to exclude background noise.
    let raw = String::from_utf8_lossy(&output.stdout);
    let mut current_exe: Option<String> = None;
    let mut current_id: u64 = 0;
    let mut is_help = false;
    let mut current_ts: u64 = 0;
    let mut current_interactive = false;

    for line in raw.lines() {
        // "----" may appear in non-raw ausearch output; handle it defensively.
        if line == "----" {
            maybe_commit(&mut current_exe, &mut is_help, &mut counts, current_ts, since, current_interactive);
            current_id = 0;
            current_ts = 0;
            current_interactive = false;
            continue;
        }

        // New event when serial number changes.
        if let Some(id) = event_serial(line) {
            if id != current_id {
                maybe_commit(&mut current_exe, &mut is_help, &mut counts, current_ts, since, current_interactive);
                current_id = id;
                current_ts = 0;
                current_interactive = false;
            }
        }

        if line.starts_with("type=SYSCALL") {
            current_ts = event_timestamp(line);
            // Only count interactive terminal sessions (tty=pts/N), not daemons.
            // Only count successful execs — failed ones mean the process was probing
            // for a binary's existence, not actually launching it.
            current_interactive = line.contains(" tty=pts") && line.contains(" success=yes ");
            for token in line.split_whitespace() {
                if let Some(raw_exe) = token.strip_prefix("exe=") {
                    let name = Path::new(raw_exe.trim_matches('"'))
                        .file_name()
                        .and_then(|n| n.to_str())
                        .unwrap_or("")
                        .to_string();
                    if !name.is_empty() {
                        current_exe = Some(name);
                    }
                    break;
                }
            }
        } else if line.starts_with("type=EXECVE") {
            for token in line.split_whitespace() {
                // Argument fields are a0=, a1=, a2=, etc.
                let is_arg = token.len() > 2
                    && token.starts_with('a')
                    && token.chars().nth(1).map_or(false, |c| c.is_ascii_digit());
                if is_arg {
                    if let Some(val) = token.splitn(2, '=').nth(1) {
                        let arg = val.trim_matches('"');
                        if arg == "--help" || arg == "-h" {
                            is_help = true;
                        }
                    }
                }
            }
        }
    }

    maybe_commit(&mut current_exe, &mut is_help, &mut counts, current_ts, since, current_interactive);
    counts
}

fn maybe_commit(
    exe: &mut Option<String>,
    is_help: &mut bool,
    counts: &mut HashMap<String, usize>,
    ts: u64,
    since: u64,
    interactive: bool,
) {
    if interactive && ts >= since {
        if let Some(name) = exe.take() {
            if !*is_help {
                *counts.entry(name).or_insert(0) += 1;
            }
        }
    } else {
        exe.take();
    }
    *is_help = false;
}

/// Extract the Unix timestamp from `msg=audit(TIMESTAMP.ms:SERIAL):`.
fn event_timestamp(line: &str) -> u64 {
    let start = match line.find("msg=audit(") {
        Some(p) => p + 10,
        None => return 0,
    };
    let rest = &line[start..];
    let dot = match rest.find('.') {
        Some(p) => p,
        None => return 0,
    };
    rest[..dot].parse().unwrap_or(0)
}

/// Extract the audit event serial number from `msg=audit(TIMESTAMP:SERIAL):`.
fn event_serial(line: &str) -> Option<u64> {
    let start = line.find("msg=audit(")? + 10;
    let rest = &line[start..];
    let colon = rest.find(':')?;
    let end = rest.find(')')?;
    if colon >= end {
        return None;
    }
    rest[colon + 1..end].parse().ok()
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
