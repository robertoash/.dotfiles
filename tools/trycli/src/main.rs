mod app;
mod audit;
mod collect;
mod ui;

use std::io;

use app::{Action, App};
use crossterm::{
    event::{self, Event},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal};

fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let refresh = args.iter().any(|a| a == "-r" || a == "--refresh");
    let stdout_mode = args.iter().any(|a| a == "--stdout");
    let help_mode = args.iter().any(|a| a == "-h" || a == "--help");

    if help_mode {
        print!(
            "trycli — browse recently installed CLI tools\n\
             \n\
             USAGE: trycli [OPTIONS]\n\
             \n\
             OPTIONS:\n\
             \x20 -r, --refresh   Force rebuild package cache\n\
             \x20 --stdout        Print list to stdout (for scripting)\n\
             \x20 -h, --help      Show this help\n\
             \n\
             KEYS:\n\
             \x20 j/k ↑↓         Navigate\n\
             \x20 g/G            First / last\n\
             \x20 <type>         Filter (any other key)\n\
             \x20 Esc            Clear filter / quit\n\
             \x20 PgDn/PgUp      Scroll preview\n\
             \x20 Ctrl+D/U       Scroll preview\n\
             \x20 r              Refresh\n\
             \x20 q              Quit\n"
        );
        return Ok(());
    }

    let packages = load_packages(refresh);
    if packages.is_empty() {
        eprintln!("No CLI tools found.");
        std::process::exit(1);
    }

    let counts = audit::get_counts();
    let auditd_ok = audit::is_running();

    if !auditd_ok && !stdout_mode {
        // Warning will appear in the TUI preview pane
    }
    if !auditd_ok && stdout_mode {
        eprintln!("warning: {}", audit::install_hint());
    }

    if stdout_mode {
        for p in &packages {
            let uses = counts.get(&p.name).copied().unwrap_or(0);
            println!(
                "{:<10}  {:<28}  {:<8}  {:>5}  {}",
                p.date_str(),
                &p.name,
                format!("({})", &p.source),
                uses,
                p.description.chars().take(60).collect::<String>()
            );
        }
        return Ok(());
    }

    // TUI
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut app = App::new(packages, counts, !auditd_ok);
    let result = run_app(&mut terminal, &mut app);

    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;

    result
}

fn run_app(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    app: &mut App,
) -> anyhow::Result<()> {
    loop {
        terminal.draw(|frame| ui::render(frame, app))?;

        match event::read()? {
            Event::Key(key) => match app.handle_key(key) {
                Action::Quit => break,
                Action::Refresh => {
                    app.show_scanning = true;
                    terminal.draw(|frame| ui::render(frame, app))?;
                    app.show_scanning = false;

                    let old_filter = app.filter.clone();
                    let pkgs = collect::build_packages();
                    collect::save_cache(&pkgs);
                    let counts = audit::get_counts();
                    let auditd_ok = audit::is_running();
                    *app = App::new(pkgs, counts, !auditd_ok);

                    if !old_filter.is_empty() {
                        app.filter = old_filter;
                        app.apply_filter();
                    }
                }
                Action::None => {}
            },
            Event::Resize(_, _) => {} // redrawn on next iteration
            _ => {}
        }
    }
    Ok(())
}

fn load_packages(force_refresh: bool) -> Vec<collect::Package> {
    if force_refresh {
        eprintln!("Scanning installed packages...");
        let pkgs = collect::build_packages();
        collect::save_cache(&pkgs);
        eprintln!("Found {} CLI tools.", pkgs.len());
        pkgs
    } else {
        collect::load_cache().unwrap_or_else(|| {
            eprintln!("Scanning installed packages...");
            let pkgs = collect::build_packages();
            collect::save_cache(&pkgs);
            eprintln!("Found {} CLI tools.", pkgs.len());
            pkgs
        })
    }
}
