mod ansi;
mod app;
mod audit;
mod collect;
mod ui;

use std::io;

use app::{Action, App};
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event},
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
             \x20 /              Filter\n\
             \x20 Esc            Exit filter / clear filter / quit\n\
             \x20 i / Enter      Toggle preview\n\
             \x20 PgDn/PgUp      Scroll preview\n\
             \x20 Ctrl+D/U       Scroll preview\n\
             \x20 Alt+h/l        Resize panes\n\
             \x20 r              Refresh\n\
             \x20 q              Quit\n"
        );
        return Ok(());
    }

    let counts = audit::get_counts();
    let auditd_ok = audit::is_running();

    if stdout_mode {
        let packages = load_packages(refresh);
        if packages.is_empty() {
            eprintln!("No CLI tools found.");
            std::process::exit(1);
        }
        if !auditd_ok {
            eprintln!("warning: {}", audit::install_hint());
        }
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

    // TUI — start with cached packages, then refresh on entry inside the TUI
    let packages = load_packages(refresh);
    if packages.is_empty() {
        eprintln!("No CLI tools found.");
        std::process::exit(1);
    }

    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut app = App::new(packages, counts, !auditd_ok);
    let result = run_app(&mut terminal, &mut app);

    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen, DisableMouseCapture)?;
    terminal.show_cursor()?;

    result
}

fn run_app(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    app: &mut App,
) -> anyhow::Result<()> {
    // Always refresh on entry to show current state
    do_refresh(terminal, app)?;

    loop {
        terminal.draw(|frame| ui::render(frame, app))?;

        // Poll with a short timeout so background preview threads can deliver results.
        if event::poll(std::time::Duration::from_millis(50))? {
            match event::read()? {
                Event::Key(key) => match app.handle_key(key) {
                    Action::Quit => break,
                    Action::Refresh => do_refresh(terminal, app)?,
                    Action::None => {}
                },
                Event::Mouse(mouse) => {
                    app.handle_mouse(mouse.kind);
                }
                Event::Resize(_, _) => {}
                _ => {}
            }
        }

        // Check if the background preview fetch finished and redraw if so.
        app.poll_preview();
    }
    Ok(())
}

fn do_refresh(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    app: &mut App,
) -> anyhow::Result<()> {
    app.show_scanning = true;
    terminal.draw(|frame| ui::render(frame, app))?;
    app.show_scanning = false;

    let old_filter = app.filter.clone();
    let old_filter_active = app.filter_active;
    let old_show_preview = app.show_preview;
    let old_split_pct = app.split_pct;
    let old_sort_by = app.sort_by;

    let pkgs = collect::build_packages();
    collect::save_cache(&pkgs);
    let counts = audit::get_counts();
    let auditd_ok = audit::is_running();
    *app = App::new(pkgs, counts, !auditd_ok);

    app.show_preview = old_show_preview;
    app.split_pct = old_split_pct;
    app.sort_by = old_sort_by;
    app.apply_sort();

    if !old_filter.is_empty() || old_filter_active {
        app.filter = old_filter;
        app.filter_active = old_filter_active;
        app.apply_filter();
    }

    // Start prefetching previews for the first 20 visible items
    app.prefetch_previews(20);

    Ok(())
}

fn load_packages(force_refresh: bool) -> Vec<collect::Package> {
    if force_refresh {
        let pkgs = collect::build_packages();
        collect::save_cache(&pkgs);
        pkgs
    } else {
        collect::load_cache().unwrap_or_else(|| {
            let pkgs = collect::build_packages();
            collect::save_cache(&pkgs);
            pkgs
        })
    }
}
