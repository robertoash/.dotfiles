use ratatui::{
    layout::{Constraint, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span, Text},
    widgets::{Block, Borders, List, ListItem, Paragraph, Wrap},
    Frame,
};

use crate::app::App;

const COL_DATE: u16 = 10;
const COL_NAME: u16 = 22;
const COL_SOURCE: u16 = 8;
const COL_USES: u16 = 6;

pub fn render(frame: &mut Frame, app: &mut App) {
    let area = frame.area();

    // Outer layout: main body + status bar
    let [main_area, status_area] =
        Layout::vertical([Constraint::Min(0), Constraint::Length(1)]).areas(area);

    // Body: list pane (left) + preview pane (right)
    let [list_area, preview_area] =
        Layout::horizontal([Constraint::Percentage(38), Constraint::Percentage(62)])
            .areas(main_area);

    render_list(frame, app, list_area);
    render_preview(frame, app, preview_area);
    render_status(frame, app, status_area);
}

fn render_list(frame: &mut Frame, app: &mut App, area: ratatui::layout::Rect) {
    let title = if app.show_scanning {
        " Scanning... ".to_string()
    } else if !app.filter.is_empty() {
        format!(" {}▌  ({}) ", app.filter, app.filtered.len())
    } else {
        format!(" Tools ({}) ", app.filtered.len())
    };

    let list_width = area.width.saturating_sub(2) as usize; // subtract borders

    let items: Vec<ListItem> = app
        .filtered
        .iter()
        .map(|&idx| {
            let p = &app.packages[idx];
            let uses = app.counts.get(&p.name).copied().unwrap_or(0);
            make_list_item(p, uses, list_width)
        })
        .collect();

    let list = List::new(items)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::DarkGray))
                .title(Span::styled(title, Style::default().fg(Color::White))),
        )
        .highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .add_modifier(Modifier::BOLD),
        );

    frame.render_stateful_widget(list, area, &mut app.list_state);
}

fn make_list_item(p: &crate::collect::Package, uses: usize, width: usize) -> ListItem<'static> {
    let date_str = format!("{:<width$} ", p.date_str(), width = COL_DATE as usize);
    let name_str = format!("{:<width$} ", truncate(&p.name, COL_NAME as usize), width = COL_NAME as usize);
    let source_str = format!("{:<width$} ", truncate(&p.source, COL_SOURCE as usize), width = COL_SOURCE as usize);
    let uses_str = format!("{:>width$} ", uses, width = COL_USES as usize);

    let fixed_len = date_str.len() + name_str.len() + source_str.len() + uses_str.len();
    let desc_width = width.saturating_sub(fixed_len);
    let desc_str = truncate(&p.description, desc_width).to_string();

    let uses_style = if uses > 0 {
        Style::default().fg(Color::Green)
    } else {
        Style::default().fg(Color::DarkGray)
    };

    let line = Line::from(vec![
        Span::styled(date_str, Style::default().fg(Color::DarkGray)),
        Span::styled(name_str, Style::default().fg(Color::White)),
        Span::styled(source_str, Style::default().fg(Color::Cyan)),
        Span::styled(uses_str, uses_style),
        Span::styled(desc_str, Style::default().fg(Color::DarkGray)),
    ]);

    ListItem::new(line)
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

fn render_status(frame: &mut Frame, _app: &App, area: ratatui::layout::Rect) {
    let parts: Vec<(&str, &str)> = vec![
        ("jk", " navigate  "),
        ("type", " filter  "),
        ("Esc", " clear  "),
        ("PgDn/PgUp", " scroll  "),
        ("r", " refresh  "),
        ("q", " quit"),
    ];

    let mut spans = Vec::new();
    for (key, desc) in parts {
        spans.push(Span::styled(
            format!(" {} ", key),
            Style::default().fg(Color::Black).bg(Color::DarkGray).add_modifier(Modifier::BOLD),
        ));
        spans.push(Span::styled(desc, Style::default().fg(Color::DarkGray)));
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
