#!/usr/bin/env python3
"""
scrape.py — Interactive launcher for the scraping toolkit.

    python scrape.py
"""

import getpass
import sys

from rich.console import Console
from rich.text import Text
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm

console = Console()

BANNER = r"""
 ____  ____  ____  ____  __ _  ____  ____
/ ___)(_  _)(_  _)(  __)/ (( \(  __)(  _ \
\___ \  )(   _)(_  ) _)(    /  ) _)  )   /
(____/ (__) (____)(____)\_)__)(____)(__\_)
"""


def rule(label):
    console.rule(f"[bold cyan]{label}[/bold cyan]", style="cyan")


def show_banner():
    console.print(f"[bold green]{BANNER}[/bold green]")
    console.print("[bold white on blue]  SITE SCRAPER TOOLKIT  [/bold white on blue]")
    console.print("[dim]Copy a site's pages and styling for design reference[/dim]\n")


def show_menu():
    console.print("[bold cyan]SELECT MODE[/bold cyan]\n")
    console.print("  [bold yellow][1][/bold yellow] Quick Scrape")
    console.print("      [dim]Regular multi-page sites — blogs, business sites, portfolios[/dim]\n")
    console.print("  [bold yellow][2][/bold yellow] Full Page Capture")
    console.print("      [dim]JS-driven pages, dashboards, dynamic content. Also saves a screenshot[/dim]\n")
    console.print("  [bold yellow][3][/bold yellow] Exit\n")


def ask_login_details():
    rule("LOGIN SETUP")
    console.print(
        "[dim]This site needs a login before scraping. Two different things are needed below —"
        " read carefully so they don't get mixed up.[/dim]\n"
    )

    console.print("[bold]A. The login page itself[/bold]")
    login_url = Prompt.ask("   Login page URL")

    console.print(
        "\n[bold]B. Field NAMES on that page[/bold] "
        "[dim](the code behind the form, not your credentials)[/dim]"
    )
    console.print(
        "   [dim]Right-click the username box on the login page -> Inspect -> "
        "find something like <input name=\"...\">[/dim]"
    )
    user_field = Prompt.ask("   Username field's name attribute", default="username")
    pass_field = Prompt.ask("   Password field's name attribute", default="password")

    console.print("\n[bold]C. Your actual login credentials[/bold]")
    username = Prompt.ask("   Your username / email")
    password = getpass.getpass("   Your password (hidden as you type): ")

    return login_url, user_field, pass_field, username, password


def run_quick_scrape():
    import site_scraper

    rule("QUICK SCRAPE")
    url = Prompt.ask("Site URL to start from")
    out_dir = Prompt.ask("Save results to folder", default="./scraped_site")
    max_pages = IntPrompt.ask("Max pages to crawl", default=30)
    delay = FloatPrompt.ask("Delay between requests, seconds", default=0.5)

    login_cfg = None
    if Confirm.ask("\nDoes this site require logging in first?", default=False):
        login_url, user_field, pass_field, username, password = ask_login_details()
        login_cfg = dict(login_url=login_url, user_field=user_field, pass_field=pass_field,
                          username=username, password=password)

    rule("RUNNING")
    with console.status("[cyan]Crawling pages...[/cyan]", spinner="line"):
        try:
            site_scraper.scrape_site(url, out_dir, max_pages, delay, login_cfg=login_cfg)
        except Exception as e:
            console.print(f"\n[bold red]FAILED:[/bold red] {e}")
            return
    console.print(f"\n[bold green]DONE.[/bold green] Results saved to: [cyan]{out_dir}[/cyan]")


def run_full_page_capture():
    import full_page_capture

    if not full_page_capture.PLAYWRIGHT_AVAILABLE:
        rule("MISSING DEPENDENCY")
        console.print("[bold red]Playwright is not installed.[/bold red]\n")
        console.print("Run these two commands, then try again:")
        console.print("  [cyan]pip install playwright[/cyan]")
        console.print("  [cyan]playwright install chromium[/cyan]")
        return

    rule("FULL PAGE CAPTURE")
    url = Prompt.ask("Page URL to capture (the page AFTER login, if any)")
    out_dir = Prompt.ask("Save results to folder", default="./captured_site")
    wait_ms = IntPrompt.ask("Extra wait for slow content, ms", default=2000)

    login_url = user_field = pass_field = username = password = None
    if Confirm.ask("\nDoes this site require logging in first?", default=False):
        login_url, user_field, pass_field, username, password = ask_login_details()

    rule("RUNNING")
    with console.status("[cyan]Rendering page and downloading assets...[/cyan]", spinner="line"):
        try:
            full_page_capture.capture(url, out_dir, login_url, user_field, pass_field,
                                       username, password, wait_ms)
        except Exception as e:
            console.print(f"\n[bold red]FAILED:[/bold red] {e}")
            return
    console.print(f"\n[bold green]DONE.[/bold green] Results saved to: [cyan]{out_dir}[/cyan]")


def main():
    show_banner()
    while True:
        show_menu()
        choice = Prompt.ask("[bold]Choose an option[/bold]", choices=["1", "2", "3"], default="1")

        if choice == "1":
            run_quick_scrape()
            break
        elif choice == "2":
            run_full_page_capture()
            break
        else:
            console.print("[dim]Exiting.[/dim]")
            sys.exit(0)


if __name__ == "__main__":
    main()
