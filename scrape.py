#!/usr/bin/env python3
"""
scrape.py — Interactive launcher for the scraping toolkit.

Run this with no arguments. It asks you a few simple questions — what kind
of site you're working with, the URL, whether it needs a login — and runs
the right tool for the job. No command-line flags to memorize.

    python scrape.py
"""

import getpass
import os
import sys

BANNER = r"""
==================================================================
  Site Scraper Toolkit
  Grab a website's pages, styling, and structure for design reference
==================================================================
"""

MODE_DESCRIPTIONS = """
Choose which tool fits the site you're copying:

  [1] Quick Scrape  (recommended for most sites)
      Fast. Follows internal links across multiple pages, downloads
      HTML, CSS, JS, images, and fonts. Best for ordinary websites
      and traditional multi-page sites (blogs, business sites,
      portfolios, server-rendered pages).

  [2] Full Page Capture  (for JS-heavy / dynamic pages)
      Slower, but more thorough. Uses a real browser to load the page,
      run its JavaScript, and capture exactly what ends up on screen —
      including content that only appears after the page finishes
      loading (dynamic widgets, filters, dashboards). Also saves a
      screenshot. Best for single-page apps, dashboards, or any page
      where Quick Scrape seems to be missing content.

  [3] Exit
"""


def ask(prompt, default=None, required=True):
    suffix = f" [{default}]" if default else ""
    while True:
        val = input(f"{prompt}{suffix}: ").strip()
        if not val and default is not None:
            return default
        if not val and not required:
            return ""
        if val:
            return val
        print("  This one's required — please enter a value.")


def ask_yes_no(prompt, default="n"):
    val = input(f"{prompt} (y/n) [{default}]: ").strip().lower()
    if not val:
        val = default
    return val.startswith("y")


def ask_login_details():
    print("\n--- Login details ---")
    print("Tip: open the login page in your browser, right-click the username box,")
    print("choose Inspect, and look for something like: <input name=\"...\">")
    login_url = ask("Login page URL (e.g. https://example.com/login)")
    user_field = ask("Username field's 'name' attribute (e.g. username, email)")
    pass_field = ask("Password field's 'name' attribute (e.g. password)")
    username = ask("Your username / email")
    password = getpass.getpass("Your password (hidden as you type): ")
    return login_url, user_field, pass_field, username, password


def run_quick_scrape():
    import site_scraper

    print("\n--- Quick Scrape setup ---")
    url = ask("URL to start scraping from (e.g. https://example.com)")
    out_dir = ask("Folder to save results into", default="./scraped_site")
    max_pages = ask("Max number of pages to crawl", default="30")
    delay = ask("Delay between requests in seconds (be polite to their server)", default="0.5")

    login_url = user_field = pass_field = username = password = None
    if ask_yes_no("Does this page require logging in first?"):
        login_url, user_field, pass_field, username, password = ask_login_details()

    login_cfg = None
    if login_url:
        login_cfg = {
            "login_url": login_url,
            "user_field": user_field,
            "pass_field": pass_field,
            "username": username,
            "password": password,
        }

    print("\nStarting Quick Scrape...\n")
    try:
        site_scraper.scrape_site(url, out_dir, int(max_pages), float(delay), login_cfg=login_cfg)
    except Exception as e:
        print(f"\n[error] Something went wrong: {e}")


def run_full_page_capture():
    import full_page_capture

    if not full_page_capture.PLAYWRIGHT_AVAILABLE:
        print("\nThis mode needs Playwright, which isn't installed yet.")
        print("Run these two commands, then come back and try again:")
        print("  pip install playwright")
        print("  playwright install chromium")
        return

    print("\n--- Full Page Capture setup ---")
    url = ask("URL of the page to capture (the page AFTER logging in, if applicable)")
    out_dir = ask("Folder to save results into", default="./captured_site")
    wait_ms = ask("Extra wait time in milliseconds for slow-loading content", default="2000")

    login_url = user_field = pass_field = username = password = None
    if ask_yes_no("Does this page require logging in first?"):
        login_url, user_field, pass_field, username, password = ask_login_details()

    print("\nStarting Full Page Capture (this opens a hidden browser, may take a moment)...\n")
    try:
        full_page_capture.capture(url, out_dir, login_url, user_field, pass_field,
                                   username, password, int(wait_ms))
    except Exception as e:
        print(f"\n[error] Something went wrong: {e}")


def main():
    print(BANNER)
    while True:
        print(MODE_DESCRIPTIONS)
        choice = ask("Enter a number", default="1")

        if choice == "1":
            run_quick_scrape()
            break
        elif choice == "2":
            run_full_page_capture()
            break
        elif choice == "3":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("\nPlease enter 1, 2, or 3.\n")


if __name__ == "__main__":
    main()
