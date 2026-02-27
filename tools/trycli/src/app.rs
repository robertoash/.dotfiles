use crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyModifiers, MouseEventKind};
use ratatui::widgets::TableState;
use std::collections::HashMap;
use std::process::Command;

use crate::collect::Package;

pub enum Action {
    None,
    Quit,
    Refresh,
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
    pub auditd_warning: bool,
    pub split_pct: u16,
}

impl App {
    pub fn new(packages: Vec<Package>, counts: HashMap<String, usize>, auditd_warning: bool) -> Self {
        let filtered: Vec<usize> = (0..packages.len()).collect();
        let mut list_state = TableState::default();
        if !filtered.is_empty() {
            list_state.select(Some(0));
        }
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
            auditd_warning,
            split_pct: 65,
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

        let sel = self.list_state.selected().unwrap_or(0);
        if self.filtered.is_empty() {
            self.list_state.select(None);
        } else if sel >= self.filtered.len() {
            self.list_state.select(Some(0));
        }
        self.preview_scroll = 0;
    }

    pub fn selected_package(&self) -> Option<&Package> {
        let idx = self.list_state.selected()?;
        let pkg_idx = *self.filtered.get(idx)?;
        Some(&self.packages[pkg_idx])
    }

    pub fn get_preview(&mut self) -> String {
        let (name, source) = match self.selected_package() {
            Some(p) => (p.name.clone(), p.source.clone()),
            None => return String::new(),
        };
        if let Some(cached) = self.help_cache.get(&name) {
            return cached.clone();
        }

        let output = Command::new(&name)
            .arg("--help")
            .env("PAGER", "cat")
            .env("MANPAGER", "cat")
            .env("GIT_PAGER", "cat")
            .env("CLICOLOR_FORCE", "1")
            .env("FORCE_COLOR", "1")
            .env("TERM", "xterm-256color")
            .output();

        let help_text = match output {
            Ok(o) => {
                let stdout = String::from_utf8_lossy(&o.stdout).into_owned();
                let stderr = String::from_utf8_lossy(&o.stderr).into_owned();
                if stdout.trim().is_empty() { stderr } else { stdout }
            }
            Err(e) => format!("Could not run --help: {}", e),
        };

        let info_text = get_package_info(&name, &source);

        let full = if info_text.trim().is_empty() {
            help_text
        } else {
            // Reset ANSI style before the separator so help colors don't bleed through
            format!("{}\x1b[0m\n\n── Package Info ──────────────────────\n{}", help_text, info_text)
        };

        self.help_cache.insert(name, full.clone());
        full
    }

    pub fn handle_key(&mut self, key: KeyEvent) -> Action {
        if key.kind != KeyEventKind::Press {
            return Action::None;
        }
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let alt = key.modifiers.contains(KeyModifiers::ALT);

        match key.code {
            KeyCode::Char('c') if ctrl => return Action::Quit,
            KeyCode::Char('h') if alt => {
                self.split_pct = self.split_pct.saturating_sub(5).max(15);
            }
            KeyCode::Char('l') if alt => {
                self.split_pct = (self.split_pct + 5).min(85);
            }

            // Esc:
            //   filter mode → exit filter mode, keep filter (allow navigation of filtered list)
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

            // Enter: confirm filter (exit filter mode) or toggle preview
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
            KeyCode::Char('g') | KeyCode::Home if !self.filter_active => self.first(),
            KeyCode::Char('G') | KeyCode::End if !self.filter_active => self.last(),

            // Preview scroll
            KeyCode::Char('d') if ctrl => self.scroll_preview_down(),
            KeyCode::Char('u') if ctrl => self.scroll_preview_up(),
            KeyCode::PageDown => self.scroll_preview_down(),
            KeyCode::PageUp => self.scroll_preview_up(),

            // /: always enter filter mode fresh (clears existing filter)
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
        }
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
        self.preview_scroll = 0;
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
        self.preview_scroll = 0;
    }

    fn first(&mut self) {
        if !self.filtered.is_empty() {
            self.list_state.select(Some(0));
            self.preview_scroll = 0;
        }
    }

    fn last(&mut self) {
        if !self.filtered.is_empty() {
            self.list_state.select(Some(self.filtered.len() - 1));
            self.preview_scroll = 0;
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
