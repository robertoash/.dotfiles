use ratatui::{
    layout::{Constraint, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span, Text},
    widgets::{Block, Borders, Cell, Paragraph, Row, Table, Wrap},
    Frame,
};

use crate::app::App;

const COL_DATE: u16 = 10;
const COL_NAME: u16 = 22;
const COL_SOURCE: u16 = 8;
const COL_USES: u16 = 5;

pub fn render(frame: &mut Frame, app: &mut App) {
    let area = frame.area();

    // Outer layout: main body + status bar
    let [main_area, status_area] =
        Layout::vertical([Constraint::Min(0), Constraint::Length(1)]).areas(area);

    // Body: list pane (left) + preview pane (right)
    let pct = app.split_pct;
    let [list_area, preview_area] =
        Layout::horizontal([Constraint::Percentage(pct), Constraint::Percentage(100 - pct)])
            .areas(main_area);

    render_list(frame, app, list_area);
    render_preview(frame, app, preview_area);
    render_status(frame, app, status_area);
}

fn render_list(frame: &mut Frame, app: &mut App, area: ratatui::layout::Rect) {
    let title = if app.show_scanning {
        " Scanning... ".to_string()
    } else if app.filter_active {
        format!(" /{}▌  ({}) ", app.filter, app.filtered.len())
    } else {
        format!(" Tools ({}) ", app.filtered.len())
    };

    let header = Row::new(vec![
        Cell::from("DATE"),
        Cell::from("NAME"),
        Cell::from("SOURCE"),
        Cell::from("USES"),
        Cell::from("DESCRIPTION"),
    ])
    .style(
        Style::default()
            .fg(Color::DarkGray)
            .add_modifier(Modifier::BOLD),
    );

    let rows: Vec<Row> = app
        .filtered
        .iter()
        .map(|&idx| {
            let p = &app.packages[idx];
            let uses = app.counts.get(&p.name).copied().unwrap_or(0);
            make_row(p, uses)
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
        .row_highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .add_modifier(Modifier::BOLD),
        )
        .column_spacing(1);

    frame.render_stateful_widget(table, area, &mut app.list_state);
}

fn make_row(p: &crate::collect::Package, uses: usize) -> Row<'static> {
    let uses_style = if uses > 0 {
        Style::default().fg(Color::Green)
    } else {
        Style::default().fg(Color::DarkGray)
    };

    Row::new(vec![
        Cell::from(p.date_str()).style(Style::default().fg(Color::DarkGray)),
        Cell::from(truncate(&p.name, COL_NAME as usize).to_string())
            .style(Style::default().fg(Color::White)),
        Cell::from(truncate(&p.source, COL_SOURCE as usize).to_string())
            .style(Style::default().fg(Color::Cyan)),
        Cell::from(if uses > 0 { uses.to_string() } else { String::new() }).style(uses_style),
        Cell::from(p.description.clone()).style(Style::default().fg(Color::DarkGray)),
    ])
}

fn render_preview(frame: &mut Frame, app: &mut App, area: ratatui::layout::Rect) {
    let (title, content) = if app.show_scanning {
        (" Scanning packages... ".to_string(), String::new())
    } else {
        let name = app
            .selected_package()
            .map(|p| format!(" {} ", p.name))
            .unwrap_or_else(|| " preview ".to_string());
        let text = app.get_preview();
        (name, text)
    };

    let warning = if app.auditd_warning {
        format!("\n\n─── Usage counts unavailable ───\n{}", crate::audit::install_hint())
    } else {
        String::new()
    };

    let full_text = if content.is_empty() && !warning.is_empty() {
        warning.trim_start_matches('\n').to_string()
    } else {
        format!("{}{}", content, warning)
    };

    let paragraph = Paragraph::new(Text::raw(full_text))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::DarkGray))
                .title(Span::styled(title, Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
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
            ("Esc", " clear "),
            ("PgDn/Up", " scroll "),
            ("Alt+hl", " resize "),
        ]
    } else {
        vec![
            ("j / k", " nav "),
            ("/", " filter "),
            ("Esc", " quit "),
            ("PgDn/Up", " scroll "),
            ("Alt+hl", " resize "),
            ("r", " refresh "),
            ("q", " quit"),
        ]
    };

    let mut spans = Vec::new();
    for (key, desc) in parts {
        spans.push(Span::styled(
            format!(" {} ", key),
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
        ));
        spans.push(Span::styled(desc, Style::default().fg(Color::White)));
    }

    let line = Line::from(spans);
    let paragraph = Paragraph::new(line);
    frame.render_widget(paragraph, area);
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
