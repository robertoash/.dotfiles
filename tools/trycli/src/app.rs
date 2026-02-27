use crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyModifiers};
use ratatui::widgets::ListState;
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
    pub list_state: ListState,
    pub filter: String,
    pub filter_active: bool,
    pub preview_scroll: u16,
    pub help_cache: HashMap<String, String>,
    pub show_scanning: bool,
    pub auditd_warning: bool,
}

impl App {
    pub fn new(packages: Vec<Package>, counts: HashMap<String, usize>, auditd_warning: bool) -> Self {
        let filtered: Vec<usize> = (0..packages.len()).collect();
        let mut list_state = ListState::default();
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
            auditd_warning,
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
        let name = match self.selected_package() {
            Some(p) => p.name.clone(),
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
            .output();
        let text = match output {
            Ok(o) => {
                let stdout = String::from_utf8_lossy(&o.stdout).into_owned();
                let stderr = String::from_utf8_lossy(&o.stderr).into_owned();
                let raw = if stdout.trim().is_empty() { stderr } else { stdout };
                strip_ansi(&raw)
            }
            Err(e) => format!("Could not run --help: {}", e),
        };
        self.help_cache.insert(name, text.clone());
        text
    }

    pub fn handle_key(&mut self, key: KeyEvent) -> Action {
        if key.kind != KeyEventKind::Press {
            return Action::None;
        }
        if key.code == KeyCode::Char('c') && key.modifiers.contains(KeyModifiers::CONTROL) {
            return Action::Quit;
        }

        if self.filter_active {
            match key.code {
                KeyCode::Esc => {
                    self.filter.clear();
                    self.filter_active = false;
                    self.apply_filter();
                }
                KeyCode::Backspace => {
                    self.filter.pop();
                    self.apply_filter();
                }
                KeyCode::Down => self.next(),
                KeyCode::Up => self.prev(),
                KeyCode::PageDown => self.scroll_preview_down(),
                KeyCode::PageUp => self.scroll_preview_up(),
                KeyCode::Char(c) => {
                    self.filter.push(c);
                    self.apply_filter();
                }
                _ => {}
            }
        } else {
            match key.code {
                KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
                KeyCode::Char('/') => self.filter_active = true,
                KeyCode::Char('r') => return Action::Refresh,
                KeyCode::Down | KeyCode::Char('j') => self.next(),
                KeyCode::Up | KeyCode::Char('k') => self.prev(),
                KeyCode::Char('g') | KeyCode::Home => self.first(),
                KeyCode::Char('G') | KeyCode::End => self.last(),
                KeyCode::PageDown => self.scroll_preview_down(),
                KeyCode::PageUp => self.scroll_preview_up(),
                KeyCode::Char('d') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                    self.scroll_preview_down();
                }
                KeyCode::Char('u') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                    self.scroll_preview_up();
                }
                _ => {}
            }
        }
        Action::None
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
                if i == 0 {
                    self.filtered.len() - 1
                } else {
                    i - 1
                }
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
        self.preview_scroll = self.preview_scroll.saturating_add(8);
    }

    fn scroll_preview_up(&mut self) {
        self.preview_scroll = self.preview_scroll.saturating_sub(8);
    }
}

fn strip_ansi(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    let mut in_esc = false;
    let mut in_csi = false;
    for ch in s.chars() {
        if in_esc {
            if ch == '[' {
                in_csi = true;
                in_esc = false;
            } else {
                in_esc = false;
            }
        } else if in_csi {
            if ch.is_ascii_alphabetic() {
                in_csi = false;
            }
        } else if ch == '\x1b' {
            in_esc = true;
        } else {
            out.push(ch);
        }
    }
    out
}
