use ratatui::{
    style::{Color, Modifier, Style},
    text::{Line, Span, Text},
};

/// Convert a string containing ANSI SGR escape codes to a ratatui `Text`.
/// Handles: bold/dim/italic/underline, standard 3/4-bit colors, 256-color, true color.
pub fn ansi_to_text(s: &str) -> Text<'static> {
    let mut lines: Vec<Line<'static>> = Vec::new();
    let mut spans: Vec<Span<'static>> = Vec::new();
    let mut style = Style::default();
    let mut buf = String::new();

    let bytes = s.as_bytes();
    let mut i = 0;

    while i < bytes.len() {
        // ESC [
        if bytes[i] == b'\x1b' && i + 1 < bytes.len() && bytes[i + 1] == b'[' {
            flush(&mut buf, style, &mut spans);
            i += 2;

            // Collect parameter string (digits and semicolons)
            let start = i;
            while i < bytes.len() && (bytes[i].is_ascii_digit() || bytes[i] == b';') {
                i += 1;
            }
            let params = &s[start..i];
            let final_byte = if i < bytes.len() { bytes[i] } else { 0 };
            i += 1; // consume final byte

            if final_byte == b'm' {
                apply_sgr(params, &mut style);
            }
            // All other CSI sequences (cursor movement etc.) are ignored
        } else if bytes[i] == b'\n' {
            flush(&mut buf, style, &mut spans);
            lines.push(Line::from(spans.clone()));
            spans.clear();
            i += 1;
        } else if bytes[i] == b'\r' {
            i += 1;
        } else {
            buf.push(bytes[i] as char);
            i += 1;
        }
    }

    flush(&mut buf, style, &mut spans);
    if !spans.is_empty() {
        lines.push(Line::from(spans));
    }

    Text::from(lines)
}

fn flush(buf: &mut String, style: Style, spans: &mut Vec<Span<'static>>) {
    if !buf.is_empty() {
        spans.push(Span::styled(buf.clone(), style));
        buf.clear();
    }
}

fn apply_sgr(params: &str, style: &mut Style) {
    let codes: Vec<u16> = if params.is_empty() {
        vec![0]
    } else {
        params.split(';').filter_map(|s| s.parse().ok()).collect()
    };

    let mut j = 0;
    while j < codes.len() {
        match codes[j] {
            0 => *style = Style::default(),
            1 => *style = style.add_modifier(Modifier::BOLD),
            2 => *style = style.add_modifier(Modifier::DIM),
            3 => *style = style.add_modifier(Modifier::ITALIC),
            4 => *style = style.add_modifier(Modifier::UNDERLINED),
            7 => *style = style.add_modifier(Modifier::REVERSED),
            22 => *style = style.remove_modifier(Modifier::BOLD | Modifier::DIM),
            23 => *style = style.remove_modifier(Modifier::ITALIC),
            24 => *style = style.remove_modifier(Modifier::UNDERLINED),
            27 => *style = style.remove_modifier(Modifier::REVERSED),
            // Standard fg (30–37), default fg (39)
            30..=37 => *style = style.fg(ansi_color(codes[j] as u8 - 30)),
            38 => {
                if let Some(c) = extended_color(&codes, j) {
                    *style = style.fg(c.0);
                    j += c.1;
                }
            }
            39 => *style = style.fg(Color::Reset),
            // Standard bg (40–47), default bg (49)
            40..=47 => *style = style.bg(ansi_color(codes[j] as u8 - 40)),
            48 => {
                if let Some(c) = extended_color(&codes, j) {
                    *style = style.bg(c.0);
                    j += c.1;
                }
            }
            49 => *style = style.bg(Color::Reset),
            // Bright fg (90–97), bright bg (100–107)
            90..=97 => *style = style.fg(ansi_color(codes[j] as u8 - 90 + 8)),
            100..=107 => *style = style.bg(ansi_color(codes[j] as u8 - 100 + 8)),
            _ => {}
        }
        j += 1;
    }
}

/// Parse extended color after a 38 or 48 code.
/// Returns (Color, extra_indices_consumed).
fn extended_color(codes: &[u16], base: usize) -> Option<(Color, usize)> {
    match codes.get(base + 1) {
        Some(&5) => {
            // 256-color: 38;5;N
            let n = *codes.get(base + 2)? as u8;
            Some((ansi_color_256(n), 2))
        }
        Some(&2) => {
            // True color: 38;2;R;G;B
            let r = *codes.get(base + 2)? as u8;
            let g = *codes.get(base + 3)? as u8;
            let b = *codes.get(base + 4)? as u8;
            Some((Color::Rgb(r, g, b), 4))
        }
        _ => None,
    }
}

fn ansi_color(n: u8) -> Color {
    match n {
        0 => Color::Black,
        1 => Color::Red,
        2 => Color::Green,
        3 => Color::Yellow,
        4 => Color::Blue,
        5 => Color::Magenta,
        6 => Color::Cyan,
        7 => Color::Gray,
        8 => Color::DarkGray,
        9 => Color::LightRed,
        10 => Color::LightGreen,
        11 => Color::LightYellow,
        12 => Color::LightBlue,
        13 => Color::LightMagenta,
        14 => Color::LightCyan,
        15 => Color::White,
        _ => Color::Reset,
    }
}

fn ansi_color_256(n: u8) -> Color {
    match n {
        0..=15 => ansi_color(n),
        16..=231 => {
            // 6×6×6 RGB cube
            let n = n - 16;
            let levels = [0u8, 95, 135, 175, 215, 255];
            Color::Rgb(levels[(n / 36) as usize], levels[((n / 6) % 6) as usize], levels[(n % 6) as usize])
        }
        232..=255 => {
            let v = 8 + (n - 232) * 10;
            Color::Rgb(v, v, v)
        }
    }
}
