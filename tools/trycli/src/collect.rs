use std::collections::HashSet;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::UNIX_EPOCH;

#[derive(Clone, Debug)]
pub struct Package {
    pub epoch: u64,
    pub name: String,
    pub source: String,
    pub description: String,
}

impl Package {
    pub fn date_str(&self) -> String {
        if self.epoch == 0 {
            "unknown   ".to_string()
        } else {
            epoch_to_date_str(self.epoch)
        }
    }
}

fn is_in_path(name: &str) -> bool {
    std::env::var("PATH")
        .unwrap_or_default()
        .split(':')
        .any(|dir| Path::new(dir).join(name).is_file())
}

// --- Pacman ---

pub fn collect_pacman() -> Vec<Package> {
    if !is_in_path("pacman") {
        return vec![];
    }
    let explicit = match Command::new("pacman").args(["-Qqet"]).output() {
        Ok(o) if o.status.success() => String::from_utf8_lossy(&o.stdout).into_owned(),
        _ => return vec![],
    };
    let names: Vec<&str> = explicit.lines().collect();
    if names.is_empty() {
        return vec![];
    }
    let info = match Command::new("pacman").arg("-Qi").args(&names).output() {
        Ok(o) if o.status.success() => String::from_utf8_lossy(&o.stdout).into_owned(),
        _ => return vec![],
    };
    parse_pacman_info(&info)
}

fn parse_pacman_info(info: &str) -> Vec<Package> {
    let mut packages = Vec::new();
    let mut name = String::new();
    let mut description = String::new();
    let mut epoch = 0u64;

    for line in info.lines() {
        if line.starts_with("Name ") {
            name = after_colon(line).to_string();
            description.clear();
            epoch = 0;
        } else if line.starts_with("Description ") {
            description = after_colon(line).to_string();
        } else if line.starts_with("Install Date") {
            epoch = parse_pacman_date(after_colon(line));
        } else if line.is_empty() && !name.is_empty() {
            if is_in_path(&name) {
                packages.push(Package {
                    epoch,
                    name: name.clone(),
                    source: "pacman".to_string(),
                    description: description.clone(),
                });
            }
            name.clear();
        }
    }
    // trailing entry without blank line
    if !name.is_empty() && is_in_path(&name) {
        packages.push(Package { epoch, name, source: "pacman".to_string(), description });
    }
    packages
}

fn after_colon(line: &str) -> &str {
    line.splitn(2, ':').nth(1).unwrap_or("").trim()
}

fn parse_pacman_date(s: &str) -> u64 {
    // "Thu 01 Feb 2024 10:23:45 AM UTC"  or  "Thu 01 Feb 2024 22:23:45 UTC"
    let parts: Vec<&str> = s.split_whitespace().collect();
    if parts.len() < 5 {
        return 0;
    }
    let day: u32 = parts[1].parse().unwrap_or(0);
    let month: u32 = match parts[2] {
        "Jan" => 1, "Feb" => 2,  "Mar" => 3,  "Apr" => 4,
        "May" => 5, "Jun" => 6,  "Jul" => 7,  "Aug" => 8,
        "Sep" => 9, "Oct" => 10, "Nov" => 11, "Dec" => 12,
        _ => return 0,
    };
    let year: i64 = parts[3].parse().unwrap_or(0);
    let time: Vec<&str> = parts[4].splitn(3, ':').collect();
    if time.len() < 3 {
        return 0;
    }
    let mut hour: u32 = time[0].parse().unwrap_or(0);
    let min: u32 = time[1].parse().unwrap_or(0);
    let sec: u32 = time[2].parse().unwrap_or(0);
    // AM/PM at index 5 if present
    if parts.len() >= 6 {
        match parts[5] {
            "PM" if hour != 12 => hour += 12,
            "AM" if hour == 12 => hour = 0,
            _ => {}
        }
    }
    date_to_epoch(year, month, day, hour, min, sec)
}

// --- Cargo ---

pub fn collect_cargo() -> Vec<Package> {
    if !is_in_path("cargo") {
        return vec![];
    }
    let output = match Command::new("cargo").args(["install", "--list"]).output() {
        Ok(o) if o.status.success() => String::from_utf8_lossy(&o.stdout).into_owned(),
        _ => return vec![],
    };
    let cargo_bin = home_dir().join(".cargo/bin");
    let mut packages = Vec::new();
    let mut crate_name = String::new();

    for line in output.lines() {
        if !line.starts_with(' ') && !line.is_empty() {
            // "ripgrep v14.1.0:"
            crate_name = line
                .rfind(" v")
                .map(|i| line[..i].trim().to_string())
                .unwrap_or_else(|| line.trim_end_matches(':').trim().to_string());
        } else if line.starts_with("    ") && !crate_name.is_empty() {
            let binary = line.trim().to_string();
            let bin_path = cargo_bin.join(&binary);
            if bin_path.exists() && is_in_path(&binary) {
                let epoch = fs::metadata(&bin_path)
                    .ok()
                    .and_then(|m| m.modified().ok())
                    .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
                    .map(|d| d.as_secs())
                    .unwrap_or(0);
                packages.push(Package {
                    epoch,
                    name: binary,
                    source: "cargo".to_string(),
                    description: format!("from crate {}", crate_name),
                });
            }
        }
    }
    packages
}

// --- Brew ---

pub fn collect_brew() -> Vec<Package> {
    if !is_in_path("brew") {
        return vec![];
    }
    let output = match Command::new("brew")
        .args(["info", "--json=v2", "--installed"])
        .output()
    {
        Ok(o) if o.status.success() => String::from_utf8_lossy(&o.stdout).into_owned(),
        _ => return vec![],
    };
    let data: serde_json::Value = serde_json::from_str(&output).unwrap_or_default();
    let mut packages = Vec::new();
    for formula in data["formulae"].as_array().cloned().unwrap_or_default() {
        let installed = formula["installed"].as_array().cloned().unwrap_or_default();
        if installed.is_empty() {
            continue;
        }
        if formula["installed_on_request"].as_bool() != Some(true) {
            continue;
        }
        let name = formula["name"].as_str().unwrap_or("").to_string();
        let desc = formula["desc"].as_str().unwrap_or("").to_string();
        let epoch = installed.last().and_then(|i| i["time"].as_u64()).unwrap_or(0);
        if !name.is_empty() && is_in_path(&name) {
            packages.push(Package { epoch, name, source: "brew".to_string(), description: desc });
        }
    }
    packages
}

// --- Build ---

pub fn build_packages() -> Vec<Package> {
    let mut seen = HashSet::new();
    let mut all = Vec::new();
    for pkg in collect_pacman()
        .into_iter()
        .chain(collect_brew())
        .chain(collect_cargo())
    {
        if seen.insert(pkg.name.clone()) {
            all.push(pkg);
        }
    }
    all.sort_by(|a, b| b.epoch.cmp(&a.epoch));
    all
}

// --- Cache ---

fn cache_path() -> PathBuf {
    let base = std::env::var("XDG_CACHE_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|_| home_dir().join(".cache"));
    base.join("trycli/packages.tsv")
}

pub fn load_cache() -> Option<Vec<Package>> {
    let path = cache_path();
    let age = fs::metadata(&path).ok()?.modified().ok()?.elapsed().ok()?.as_secs();
    if age > 86400 {
        return None;
    }
    let content = fs::read_to_string(&path).ok()?;
    let packages = content
        .lines()
        .filter_map(|line| {
            let mut parts = line.splitn(4, '\t');
            Some(Package {
                epoch: parts.next()?.parse().ok()?,
                name: parts.next()?.to_string(),
                source: parts.next()?.to_string(),
                description: parts.next().unwrap_or("").to_string(),
            })
        })
        .collect();
    Some(packages)
}

pub fn save_cache(packages: &[Package]) {
    let path = cache_path();
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    if let Ok(mut f) = fs::File::create(&path) {
        for p in packages {
            let _ = writeln!(f, "{}\t{}\t{}\t{}", p.epoch, p.name, p.source, p.description);
        }
    }
}

// --- Date helpers ---

fn home_dir() -> PathBuf {
    std::env::var("HOME").map(PathBuf::from).unwrap_or_else(|_| PathBuf::from("/tmp"))
}

fn date_to_epoch(year: i64, month: u32, day: u32, hour: u32, min: u32, sec: u32) -> u64 {
    let y = if month <= 2 { year - 1 } else { year };
    let m = if month <= 2 { month as i64 + 12 } else { month as i64 };
    let d = day as i64;
    let jdn = d + (153 * m + 2) / 5 + 365 * y + y / 4 - y / 100 + y / 400 - 32045;
    let unix_day = jdn - 2440588;
    if unix_day < 0 {
        return 0;
    }
    (unix_day as u64) * 86400 + (hour as u64) * 3600 + (min as u64) * 60 + sec as u64
}

pub fn epoch_to_date_str(epoch: u64) -> String {
    let days = (epoch / 86400) as i64;
    let jd = days + 2440588;
    let a = jd + 32044;
    let b = (4 * a + 3) / 146097;
    let c = a - (146097 * b) / 4;
    let d = (4 * c + 3) / 1461;
    let e = c - (1461 * d) / 4;
    let m = (5 * e + 2) / 153;
    let day = e - (153 * m + 2) / 5 + 1;
    let month = m + 3 - 12 * (m / 10);
    let year = 100 * b + d - 4800 + m / 10;
    format!("{:04}-{:02}-{:02}", year, month, day)
}
