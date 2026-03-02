use ratatui::{
    layout::{Alignment, Constraint, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span, Text},
    widgets::{Block, Borders, Cell, Paragraph, Row, Table, Wrap},
    Frame,
};

use crate::ansi::ansi_to_text;
use crate::app::{App, SortBy};

const COL_DATE: u16 = 10;
const COL_NAME: u16 = 22;
const COL_SOURCE: u16 = 8;
const COL_USES: u16 = 5;

const COL_BG_DARK: Color = Color::Rgb(18, 18, 18);
const COL_BG_LIGHT: Color = Color::Rgb(30, 30, 30);
const COL_BG_SEL: Color = Color::Rgb(60, 60, 60);

fn col_bg(col: usize, is_selected: bool) -> Color {
    if is_selected {
        COL_BG_SEL
    } else if col % 2 == 0 {
        COL_BG_DARK
    } else {
        COL_BG_LIGHT
    }
}

pub fn render(frame: &mut Frame, app: &mut App) {
    let area = frame.area();

    let [main_area, status_area] =
        Layout::vertical([Constraint::Min(0), Constraint::Length(1)]).areas(area);

    if app.show_preview {
        let pct = app.split_pct;
        let [list_area, preview_area] =
            Layout::horizontal([Constraint::Percentage(pct), Constraint::Percentage(100 - pct)])
                .areas(main_area);
        render_list(frame, app, list_area);
        render_preview(frame, app, preview_area);
    } else {
        render_list(frame, app, main_area);
    }

    render_status(frame, app, status_area);
}

fn render_list(frame: &mut Frame, app: &mut App, area: ratatui::layout::Rect) {
    let title = if app.show_scanning {
        " Scanning... ".to_string()
    } else if app.filter_active {
        format!(" /{}▌  ({}) ", app.filter, app.filtered.len())
    } else if !app.filter.is_empty() {
        format!(" /{}  ({}) ", app.filter, app.filtered.len())
    } else {
        format!(" Tools ({}) ", app.filtered.len())
    };

    let header_style = Style::default().fg(Color::DarkGray).add_modifier(Modifier::BOLD);
    let sort_style = Style::default().fg(Color::White).add_modifier(Modifier::BOLD);
    let s = app.sort_by;
    let dir = if app.sort_asc { " ▲" } else { " ▼" };
    let header = Row::new(vec![
        Cell::from(if s == SortBy::Date { format!("DATE{dir}") } else { "DATE".into() })
            .style(if s == SortBy::Date { sort_style } else { header_style }.bg(col_bg(0, false))),
        Cell::from(if s == SortBy::Name { format!("NAME{dir}") } else { "NAME".into() })
            .style(if s == SortBy::Name { sort_style } else { header_style }.bg(col_bg(1, false))),
        Cell::from(if s == SortBy::Source { format!("SRC{dir}") } else { "SOURCE".into() })
            .style(if s == SortBy::Source { sort_style } else { header_style }.bg(col_bg(2, false))),
        Cell::from(Text::raw({
            let uses_hdr = if s == SortBy::Uses { format!("USE{dir}") } else { "USES".into() };
            center_str(&uses_hdr, COL_USES as usize)
        }))
            .style(if s == SortBy::Uses { sort_style } else { header_style }.bg(col_bg(3, false))),
        Cell::from("DESCRIPTION").style(header_style.bg(col_bg(4, false))),
    ]);

    let selected = app.list_state.selected();
    let rows: Vec<Row> = app
        .filtered
        .iter()
        .enumerate()
        .map(|(i, &idx)| {
            let p = &app.packages[idx];
            let uses = app.counts.get(&p.name).copied().unwrap_or(0);
            make_row(p, uses, selected == Some(i))
        })
        .collect();

    let widths = [
        Constraint::Length(COL_DATE),
        Constraint::Length(COL_NAME),
        Constraint::Length(COL_SOURCE),
        Constraint::Length(COL_USES),
        Constraint::Min(0),
    ];

    let table = Table::new(rows, widths)
        .header(header)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::DarkGray))
                .title(Span::styled(title, Style::default().fg(Color::White))),
        )
        .row_highlight_style(Style::default().add_modifier(Modifier::BOLD))
        .column_spacing(1);

    frame.render_stateful_widget(table, area, &mut app.list_state);
}

fn make_row(p: &crate::collect::Package, uses: usize, is_selected: bool) -> Row<'static> {
    let uses_style = if uses > 0 {
        Style::default().fg(Color::Green).bg(col_bg(3, is_selected))
    } else {
        Style::default().fg(Color::DarkGray).bg(col_bg(3, is_selected))
    };

    let uses_str = if uses > 0 {
        center_str(&uses.to_string(), COL_USES as usize)
    } else {
        " ".repeat(COL_USES as usize)
    };

    Row::new(vec![
        Cell::from(p.date_str())
            .style(Style::default().fg(Color::DarkGray).bg(col_bg(0, is_selected))),
        Cell::from(truncate(&p.name, COL_NAME as usize).to_string())
            .style(Style::default().fg(Color::White).bg(col_bg(1, is_selected))),
        Cell::from(truncate(&p.source, COL_SOURCE as usize).to_string())
            .style(Style::default().fg(Color::DarkGray).bg(col_bg(2, is_selected))),
        Cell::from(uses_str).style(uses_style),
        Cell::from(p.description.clone())
            .style(Style::default().fg(Color::DarkGray).bg(col_bg(4, is_selected))),
    ])
}

fn render_preview(frame: &mut Frame, app: &App, area: ratatui::layout::Rect) {
    let title = if app.show_scanning {
        " Scanning packages... ".to_string()
    } else if app.preview_loading {
        app.selected_package()
            .map(|p| format!(" {} — loading… ", p.name))
            .unwrap_or_else(|| " loading… ".to_string())
    } else {
        app.selected_package()
            .map(|p| format!(" {} ", p.name))
            .unwrap_or_else(|| " preview ".to_string())
    };

    let warning = if app.auditd_warning {
        format!("\n\n─── Usage counts unavailable ───\n{}", crate::audit::install_hint())
    } else {
        String::new()
    };

    let raw = if app.show_scanning {
        String::new()
    } else {
        let content = app.get_preview();
        if content.is_empty() && !warning.is_empty() {
            warning.trim_start_matches('\n').to_string()
        } else {
            format!("{}{}", content, warning)
        }
    };

    let text: Text = ansi_to_text(&raw);

    let paragraph = Paragraph::new(text)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::DarkGray))
                .title(Span::styled(
                    title,
                    Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
                )),
        )
        .wrap(Wrap { trim: false })
        .scroll((app.preview_scroll, 0));

    frame.render_widget(paragraph, area);
}

fn render_status(frame: &mut Frame, app: &App, area: ratatui::layout::Rect) {
    let parts: Vec<(&str, &str)> = if app.filter_active {
        vec![
            ("j / k", " nav "),
            ("type", " filter "),
            ("Enter", " confirm "),
            ("Esc", " exit "),
        ]
    } else if !app.filter.is_empty() {
        vec![
            ("j / k", " nav "),
            ("/", " re-filter "),
            ("Esc", " clear "),
            ("i", if app.show_preview { " close " } else { " preview " }),
            ("r", " refresh "),
            ("q", " quit"),
        ]
    } else if app.show_preview {
        vec![
            ("j/k/J/K", " nav "),
            ("/", " filter "),
            ("i", " close "),
            ("PgDn/Up", " scroll "),
            ("Alt+hl", " resize "),
            ("r", " refresh "),
            ("q", " quit"),
        ]
    } else {
        vec![
            ("j/k/J/K", " nav "),
            ("/", " filter "),
            ("i", " preview "),
            (",d/n/s/u", " sort "),
            ("r", " refresh "),
            ("q", " quit"),
        ]
    };

    let key_bg = Color::Rgb(45, 45, 45);
    let mut spans = Vec::new();
    for (key, desc) in parts {
        spans.push(Span::styled(
            format!(" {} ", key),
            Style::default().fg(Color::Yellow).bg(key_bg).add_modifier(Modifier::BOLD),
        ));
        spans.push(Span::styled(desc, Style::default().fg(Color::White)));
    }

    if app.show_scanning {
        // Right-aligned "Refreshing…" indicator.
        let notice = "  Refreshing…  ";
        let notice_style = Style::default()
            .fg(Color::Black)
            .bg(Color::Yellow)
            .add_modifier(Modifier::BOLD);
        let [left_area, right_area] = Layout::horizontal([
            Constraint::Min(0),
            Constraint::Length(notice.chars().count() as u16),
        ])
        .areas(area);
        frame.render_widget(Paragraph::new(Line::from(spans)), left_area);
        frame.render_widget(
            Paragraph::new(notice).style(notice_style).alignment(Alignment::Right),
            right_area,
        );
    } else {
        frame.render_widget(Paragraph::new(Line::from(spans)), area);
    }
}

fn center_str(s: &str, width: usize) -> String {
    let len = s.chars().count();
    if len >= width {
        return s.to_string();
    }
    let pad_total = width - len;
    let pad_left = (pad_total + 1) / 2;
    let pad_right = pad_total - pad_left;
    format!("{}{}{}", " ".repeat(pad_left), s, " ".repeat(pad_right))
}

fn truncate(s: &str, max: usize) -> &str {
    if s.len() <= max {
        s
    } else {
        let mut end = max;
        while !s.is_char_boundary(end) {
            end -= 1;
        }
        &s[..end]
    }
}
