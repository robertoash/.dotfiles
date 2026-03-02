use crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyModifiers, MouseEventKind};
use ratatui::widgets::TableState;
use std::collections::HashMap;
use std::process::{Command, Stdio};
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};

use crate::collect::Package;

pub enum Action {
    None,
    Quit,
    Refresh,
}

#[derive(Clone, Copy, PartialEq)]
pub enum SortBy {
    Date,
    Name,
    Source,
    Uses,
}

impl SortBy {
    /// Default ascending direction for this column (false = descending).
    fn default_asc(self) -> bool {
        match self {
            SortBy::Date | SortBy::Uses => false, // newest/most-used first
            SortBy::Name | SortBy::Source => true, // A-Z
        }
    }
}

pub struct App {
    pub packages: Vec<Package>,
    pub counts: HashMap<String, usize>,
    pub filtered: Vec<usize>,
    pub list_state: TableState,
    pub filter: String,
    pub filter_active: bool,
    pub preview_scroll: u16,
    pub help_cache: HashMap<String, String>,
    pub show_scanning: bool,
    pub show_preview: bool,
    pub preview_loading: bool,
    pub auditd_warning: bool,
    pub split_pct: u16,
    pub sort_by: SortBy,
    pub sort_asc: bool,
    pub pending_sort: bool,
    preview_rx: Option<mpsc::Receiver<(String, String)>>,
    prefetch_tx: mpsc::Sender<(String, String)>,
    prefetch_rx: mpsc::Receiver<(String, String)>,
    prefetch_pending: std::collections::HashSet<String>,
}

impl App {
    pub fn new(packages: Vec<Package>, counts: HashMap<String, usize>, auditd_warning: bool) -> Self {
        let filtered: Vec<usize> = (0..packages.len()).collect();
        let mut list_state = TableState::default();
        if !filtered.is_empty() {
            list_state.select(Some(0));
        }
        let (prefetch_tx, prefetch_rx) = mpsc::channel();
        Self {
            packages,
            counts,
            filtered,
            list_state,
            filter: String::new(),
            filter_active: false,
            preview_scroll: 0,
            help_cache: HashMap::new(),
            show_scanning: false,
            show_preview: false,
            preview_loading: false,
            auditd_warning,
            split_pct: 65,
            sort_by: SortBy::Date,
            sort_asc: SortBy::Date.default_asc(),
            pending_sort: false,
            preview_rx: None,
            prefetch_tx,
            prefetch_rx,
            prefetch_pending: std::collections::HashSet::new(),
        }
    }

    pub fn apply_filter(&mut self) {
        let q = self.filter.to_lowercase();
        self.filtered = (0..self.packages.len())
            .filter(|&i| {
                let p = &self.packages[i];
                q.is_empty()
                    || p.name.to_lowercase().contains(&q)
                    || p.source.to_lowercase().contains(&q)
                    || p.description.to_lowercase().contains(&q)
            })
            .collect();

        self.apply_sort();

        let sel = self.list_state.selected().unwrap_or(0);
        if self.filtered.is_empty() {
            self.list_state.select(None);
        } else if sel >= self.filtered.len() {
            self.list_state.select(Some(0));
        }
        self.preview_scroll = 0;
    }

    pub fn apply_sort(&mut self) {
        let packages = &self.packages;
        let counts = &self.counts;
        let sort_by = self.sort_by;
        let asc = self.sort_asc;
        self.filtered.sort_by(|&a, &b| {
            // Primary sort: always computed low→high, then reversed if descending.
            let primary = match sort_by {
                SortBy::Date => packages[a].epoch.cmp(&packages[b].epoch),
                SortBy::Name => packages[a].name.cmp(&packages[b].name),
                SortBy::Source => packages[a].source.cmp(&packages[b].source),
                SortBy::Uses => {
                    let ua = counts.get(&packages[a].name).copied().unwrap_or(0);
                    let ub = counts.get(&packages[b].name).copied().unwrap_or(0);
                    ua.cmp(&ub)
                }
            };
            let ordered = if asc { primary } else { primary.reverse() };
            // Secondary: always by date DESC for ties.
            ordered.then(packages[b].epoch.cmp(&packages[a].epoch))
        });
    }

    pub fn selected_package(&self) -> Option<&Package> {
        let idx = self.list_state.selected()?;
        let pkg_idx = *self.filtered.get(idx)?;
        Some(&self.packages[pkg_idx])
    }

    /// Returns cached preview content, or an empty string if still loading.
    pub fn get_preview(&self) -> String {
        match self.selected_package() {
            Some(p) => self.help_cache.get(&p.name).cloned().unwrap_or_default(),
            None => String::new(),
        }
    }

    /// Kick off a background thread to fetch preview content for the current selection.
    /// Drops any in-flight request for a previous selection.
    pub fn request_preview(&mut self) {
        let (name, source) = match self.selected_package() {
            Some(p) => (p.name.clone(), p.source.clone()),
            None => return,
        };
        if self.help_cache.contains_key(&name) {
            self.preview_loading = false;
            self.preview_rx = None;
            return;
        }
        let (tx, rx) = mpsc::channel();
        self.preview_loading = true;
        self.preview_rx = Some(rx);
        thread::spawn(move || {
            let help_text = tldr_or_help(&name);
            let info_text = get_package_info(&name, &source);
            let full = if info_text.trim().is_empty() {
                help_text
            } else {
                format!("{}\x1b[0m\n\n── Package Info ──────────────────────\n{}", help_text, info_text)
            };
            let _ = tx.send((name, full));
        });
    }

    /// Check if any background preview threads have finished. Returns true if the
    /// display should be redrawn.
    pub fn poll_preview(&mut self) -> bool {
        let mut changed = false;

        // Drain prefetch results
        while let Ok((name, content)) = self.prefetch_rx.try_recv() {
            self.prefetch_pending.remove(&name);
            self.help_cache.insert(name, content);
            changed = true;
        }

        // Check the selected-item preview channel
        let result = if let Some(rx) = &self.preview_rx {
            rx.try_recv().ok()
        } else {
            return changed;
        };
        if let Some((name, content)) = result {
            self.help_cache.insert(name, content);
            self.preview_loading = false;
            self.preview_rx = None;
            true
        } else {
            changed
        }
    }

    /// Prefetch previews for the first N visible items in the background.
    pub fn prefetch_previews(&mut self, count: usize) {
        for &idx in self.filtered.iter().take(count) {
            let p = &self.packages[idx];
            if self.help_cache.contains_key(&p.name) || self.prefetch_pending.contains(&p.name) {
                continue;
            }
            self.prefetch_pending.insert(p.name.clone());
            let name = p.name.clone();
            let source = p.source.clone();
            let tx = self.prefetch_tx.clone();
            thread::spawn(move || {
                let help_text = tldr_or_help(&name);
                let info_text = get_package_info(&name, &source);
                let full = if info_text.trim().is_empty() {
                    help_text
                } else {
                    format!("{}\x1b[0m\n\n── Package Info ──────────────────────\n{}", help_text, info_text)
                };
                let _ = tx.send((name, full));
            });
        }
    }

    pub fn handle_key(&mut self, key: KeyEvent) -> Action {
        if key.kind != KeyEventKind::Press {
            return Action::None;
        }
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let alt = key.modifiers.contains(KeyModifiers::ALT);

        // Consume pending sort prefix
        if self.pending_sort {
            self.pending_sort = false;
            if !self.filter_active {
                let new_sort = match key.code {
                    KeyCode::Char('d') => Some(SortBy::Date),
                    KeyCode::Char('n') => Some(SortBy::Name),
                    KeyCode::Char('s') => Some(SortBy::Source),
                    KeyCode::Char('u') => Some(SortBy::Uses),
                    _ => None,
                };
                if let Some(col) = new_sort {
                    if col == self.sort_by {
                        // Same column: toggle direction
                        self.sort_asc = !self.sort_asc;
                    } else {
                        // New column: switch and reset to default direction
                        self.sort_by = col;
                        self.sort_asc = col.default_asc();
                    }
                    self.apply_sort();
                }
            }
            return Action::None;
        }

        match key.code {
            KeyCode::Char('c') if ctrl => return Action::Quit,
            KeyCode::Char('h') if alt => {
                self.split_pct = self.split_pct.saturating_sub(5).max(15);
            }
            KeyCode::Char('l') if alt => {
                self.split_pct = (self.split_pct + 5).min(85);
            }

            // Esc:
            //   filter mode → exit filter mode, keep filter
            //   normal mode + filter → clear filter
            //   normal mode, no filter → quit
            KeyCode::Esc => {
                if self.filter_active {
                    self.filter_active = false;
                } else if !self.filter.is_empty() {
                    self.filter.clear();
                    self.apply_filter();
                } else {
                    return Action::Quit;
                }
            }

            // Enter: confirm filter or toggle preview
            KeyCode::Enter => {
                if self.filter_active {
                    self.filter_active = false;
                } else {
                    self.toggle_preview();
                }
            }

            // Navigation always works
            KeyCode::Char('j') | KeyCode::Down => self.next(),
            KeyCode::Char('k') | KeyCode::Up => self.prev(),
            KeyCode::Char('J') if !self.filter_active => self.jump_by(5),
            KeyCode::Char('K') if !self.filter_active => self.jump_by(-5),
            KeyCode::Char('g') | KeyCode::Home if !self.filter_active => self.first(),
            KeyCode::Char('G') | KeyCode::End if !self.filter_active => self.last(),

            // Ctrl+D/U and PgDn/PgUp: scroll preview when open, jump list when not
            KeyCode::Char('d') if ctrl => {
                if self.show_preview { self.scroll_preview_down(); } else { self.jump_by(10); }
            }
            KeyCode::Char('u') if ctrl => {
                if self.show_preview { self.scroll_preview_up(); } else { self.jump_by(-10); }
            }
            KeyCode::PageDown => {
                if self.show_preview { self.scroll_preview_down(); } else { self.jump_by(10); }
            }
            KeyCode::PageUp => {
                if self.show_preview { self.scroll_preview_up(); } else { self.jump_by(-10); }
            }

            // /: always enter filter mode fresh
            KeyCode::Char('/') if !self.filter_active => {
                if !self.filter.is_empty() {
                    self.filter.clear();
                    self.apply_filter();
                }
                self.filter_active = true;
            }

            // Filter editing (only in filter mode)
            KeyCode::Backspace if self.filter_active => {
                self.filter.pop();
                self.apply_filter();
            }

            // Normal-mode single-key actions
            KeyCode::Char(',') if !self.filter_active => {
                self.pending_sort = true;
            }
            KeyCode::Char('i') if !self.filter_active => self.toggle_preview(),
            KeyCode::Char('q') if !self.filter_active => return Action::Quit,
            KeyCode::Char('r') if !self.filter_active => return Action::Refresh,

            // Characters go to filter only in filter mode
            KeyCode::Char(c) if self.filter_active => {
                self.filter.push(c);
                self.apply_filter();
            }
            _ => {}
        }
        Action::None
    }

    pub fn handle_mouse(&mut self, kind: MouseEventKind) {
        if !self.show_preview {
            return;
        }
        match kind {
            MouseEventKind::ScrollDown => {
                self.preview_scroll = self.preview_scroll.saturating_add(3);
            }
            MouseEventKind::ScrollUp => {
                self.preview_scroll = self.preview_scroll.saturating_sub(3);
            }
            _ => {}
        }
    }

    fn toggle_preview(&mut self) {
        if self.show_preview {
            self.show_preview = false;
        } else {
            self.show_preview = true;
            self.split_pct = 65;
            self.preview_scroll = 0;
            self.request_preview();
        }
    }

    fn on_selection_change(&mut self) {
        self.preview_scroll = 0;
        if self.show_preview {
            self.request_preview();
        }
    }

    fn jump_by(&mut self, delta: i32) {
        if self.filtered.is_empty() {
            return;
        }
        let len = self.filtered.len() as i32;
        let cur = self.list_state.selected().unwrap_or(0) as i32;
        let new = (cur + delta).clamp(0, len - 1) as usize;
        self.list_state.select(Some(new));
        self.on_selection_change();
    }

    fn next(&mut self) {
        if self.filtered.is_empty() {
            return;
        }
        let i = match self.list_state.selected() {
            Some(i) => (i + 1) % self.filtered.len(),
            None => 0,
        };
        self.list_state.select(Some(i));
        self.on_selection_change();
    }

    fn prev(&mut self) {
        if self.filtered.is_empty() {
            return;
        }
        let i = match self.list_state.selected() {
            Some(i) => {
                if i == 0 { self.filtered.len() - 1 } else { i - 1 }
            }
            None => 0,
        };
        self.list_state.select(Some(i));
        self.on_selection_change();
    }

    fn first(&mut self) {
        if !self.filtered.is_empty() {
            self.list_state.select(Some(0));
            self.on_selection_change();
        }
    }

    fn last(&mut self) {
        if !self.filtered.is_empty() {
            self.list_state.select(Some(self.filtered.len() - 1));
            self.on_selection_change();
        }
    }

    fn scroll_preview_down(&mut self) {
        if self.show_preview {
            self.preview_scroll = self.preview_scroll.saturating_add(8);
        }
    }

    fn scroll_preview_up(&mut self) {
        if self.show_preview {
            self.preview_scroll = self.preview_scroll.saturating_sub(8);
        }
    }
}

const CMD_TIMEOUT: Duration = Duration::from_secs(4);

/// Run a command with a timeout. Kills the child if it exceeds the deadline.
fn run_with_timeout(mut child: std::process::Child) -> Option<std::process::Output> {
    let start = Instant::now();
    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                let stdout = child.stdout.take().map(|mut r| {
                    let mut buf = Vec::new();
                    std::io::Read::read_to_end(&mut r, &mut buf).ok();
                    buf
                }).unwrap_or_default();
                let stderr = child.stderr.take().map(|mut r| {
                    let mut buf = Vec::new();
                    std::io::Read::read_to_end(&mut r, &mut buf).ok();
                    buf
                }).unwrap_or_default();
                return Some(std::process::Output { status, stdout, stderr });
            }
            Ok(None) => {
                if start.elapsed() > CMD_TIMEOUT {
                    let _ = child.kill();
                    let _ = child.wait();
                    return None;
                }
                thread::sleep(Duration::from_millis(50));
            }
            Err(_) => return None,
        }
    }
}

fn tldr_or_help(name: &str) -> String {
    // Prefer tldr if available
    if is_in_path("tldr") {
        if let Ok(child) = Command::new("tldr")
            .args(["--color", "always", name])
            .env("PAGER", "cat")
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
        {
            if let Some(o) = run_with_timeout(child) {
                if o.status.success() {
                    let text = String::from_utf8_lossy(&o.stdout).into_owned();
                    if !text.trim().is_empty() {
                        return text;
                    }
                }
            }
        }
    }

    // Direct execution with color env vars + timeout
    match Command::new(name)
        .arg("--help")
        .env("PAGER", "cat")
        .env("MANPAGER", "cat")
        .env("GIT_PAGER", "cat")
        .env("CLICOLOR_FORCE", "1")
        .env("FORCE_COLOR", "1")
        .env("TERM", "xterm-256color")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(child) => match run_with_timeout(child) {
            Some(o) => {
                let stdout = String::from_utf8_lossy(&o.stdout).into_owned();
                let stderr = String::from_utf8_lossy(&o.stderr).into_owned();
                if stdout.trim().is_empty() { stderr } else { stdout }
            }
            None => format!("{}: timed out (interactive tool?)", name),
        },
        Err(e) => format!("Could not run --help: {}", e),
    }
}

fn get_package_info(name: &str, source: &str) -> String {
    match source {
        "pacman" => Command::new("pacman")
            .args(["-Qi", name])
            .output()
            .ok()
            .map(|o| {
                let s = String::from_utf8_lossy(&o.stdout).into_owned();
                if s.trim().is_empty() {
                    String::from_utf8_lossy(&o.stderr).into_owned()
                } else {
                    s
                }
            })
            .unwrap_or_default(),
        "brew" => Command::new("brew")
            .args(["info", name])
            .output()
            .ok()
            .map(|o| String::from_utf8_lossy(&o.stdout).into_owned())
            .unwrap_or_default(),
        _ => String::new(),
    }
}

fn is_in_path(name: &str) -> bool {
    std::env::var("PATH")
        .unwrap_or_default()
        .split(':')
        .any(|d| std::path::Path::new(d).join(name).is_file())
}
