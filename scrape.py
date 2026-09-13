#!/usr/bin/env python3
"""
scrape.py — Interactive launcher for the scraping toolkit.

    python scrape.py

Answer a few short questions, get a site scraped. No flags to memorize.
"""

import getpass
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
from rich import box

console = Console()


def show_banner():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]SITE SCRAPER TOOLKIT[/bold cyan]\n"
        "[dim]Grab a site's pages & styling for design reference[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
    ))


def show_menu():
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE_HEAVY)
    table.add_column("#", style="bold cyan", width=3)
    table.add_column("Mode", style="bold")
    table.add_column("Best for")

    table.add_row("1", "⚡ Quick Scrape", "Regular multi-page sites (blogs, business, portfolios)")
    table.add_row("2", "🌐 Full Page Capture", "JS-heavy pages, dashboards, dynamic content + screenshot")
    table.add_row("3", "🚪 Exit", "")

    console.print(table)
    console.print()


def ask_login_details():
    console.print("\n[bold yellow]🔒 Login details[/bold yellow]")
    console.print("[dim]Tip: right-click the username field on the login page → Inspect → find name=\"...\"[/dim]\n")
    login_url = Prompt.ask("Login page URL")
    user_field = Prompt.ask("Username field name", default="username")
    pass_field = Prompt.ask("Password field name", default="password")
    username = Prompt.ask("Your username / email")
    password = getpass.getpass("Your password (hidden): ")
    return login_url, user_field, pass_field, username, password


def run_quick_scrape():
    import site_scraper

    console.print(Panel("[bold cyan]⚡ Quick Scrape[/bold cyan]", box=box.MINIMAL))
    url = Prompt.ask("URL to start from")
    out_dir = Prompt.ask("Save to folder", default="./scraped_site")
    max_pages = IntPrompt.ask("Max pages to crawl", default=30)
    delay = FloatPrompt.ask("Delay between requests (sec)", default=0.5)

    login_cfg = None
    if Confirm.ask("Needs login first?", default=False):
        login_url, user_field, pass_field, username, password = ask_login_details()
        login_cfg = dict(login_url=login_url, user_field=user_field, pass_field=pass_field,
                          username=username, password=password)

    console.print("\n[bold green]▶ Running...[/bold green]\n")
    with console.status("[cyan]Crawling pages...", spinner="dots"):
        try:
            site_scraper.scrape_site(url, out_dir, max_pages, delay, login_cfg=login_cfg)
        except Exception as e:
            console.print(f"[bold red]✗ Error:[/bold red] {e}")
            return
    console.print(f"\n[bold green]✓ Done![/bold green] Open [cyan]{out_dir}[/cyan] to view your files.")


def run_full_page_capture():
    import full_page_capture

    if not full_page_capture.PLAYWRIGHT_AVAILABLE:
        console.print(Panel(
            "[bold red]Playwright not installed[/bold red]\n\n"
            "Run these, then try again:\n"
            "[cyan]pip install playwright\nplaywright install chromium[/cyan]",
            border_style="red",
        ))
        return

    console.print(Panel("[bold cyan]🌐 Full Page Capture[/bold cyan]", box=box.MINIMAL))
    url = Prompt.ask("Page URL to capture (after login, if any)")
    out_dir = Prompt.ask("Save to folder", default="./captured_site")
    wait_ms = IntPrompt.ask("Extra wait for slow content (ms)", default=2000)

    login_url = user_field = pass_field = username = password = None
    if Confirm.ask("Needs login first?", default=False):
        login_url, user_field, pass_field, username, password = ask_login_details()

    console.print("\n[bold green]▶ Launching browser...[/bold green]\n")
    with console.status("[cyan]Rendering page & downloading assets...", spinner="dots"):
        try:
            full_page_capture.capture(url, out_dir, login_url, user_field, pass_field,
                                       username, password, wait_ms)
        except Exception as e:
            console.print(f"[bold red]✗ Error:[/bold red] {e}")
            return
    console.print(f"\n[bold green]✓ Done![/bold green] Open [cyan]{out_dir}[/cyan] to view your files.")


def main():
    show_banner()
    while True:
        show_menu()
        choice = Prompt.ask("Choose", choices=["1", "2", "3"], default="1")

        if choice == "1":
            run_quick_scrape()
            break
        elif choice == "2":
            run_full_page_capture()
            break
        else:
            console.print("[dim]Goodbye 👋[/dim]")
            sys.exit(0)


if __name__ == "__main__":
    main()
