#!/usr/bin/env python3
"""
full_page_capture.py — Capture the FULL rendered version of a logged-in page:
final HTML (after JavaScript runs), every CSS/JS/image/font file actually
loaded, and a full-page screenshot for visual reference.

Unlike site_scraper.py (which only sees raw server HTML), this drives a real
headless browser, so it also captures content that JavaScript builds after
the page loads (dynamic widgets, filtered lists, lazy-loaded images, fonts
pulled in via CSS, etc).

SETUP (one-time):
    pip install playwright
    playwright install chromium

USAGE:
    python full_page_capture.py https://example.com/dashboard \\
        --out ./captured_site \\
        --login-url https://example.com/login \\
        --login-user-field username --login-pass-field password

    Credentials come from SITE_USER / SITE_PASS environment variables:
        $env:SITE_USER="yourusername"      (PowerShell)
        $env:SITE_PASS="yourpassword"

    Omit --login-url entirely if the page doesn't need a login.

OUTPUT:
    ./captured_site/<domain>/login.html            — login page (if --login-url given)
    ./captured_site/<domain>/login_screenshot.png  — screenshot of the login page
    ./captured_site/<domain>/page.html             — target page, final rendered HTML
    ./captured_site/<domain>/page_screenshot.png   — screenshot of the target page
    ./captured_site/<domain>/...                   — every CSS/JS/image/font file used, in its original path structure

ETHICAL/LEGAL NOTE:
    Only use this against sites/accounts you're authorized to access. This is
    for studying layout/styling to build something new — not for republishing
    someone else's copyrighted content or private data as your own.
"""

import argparse
import os
import re
import sys
import urllib.parse as urlparse

from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

SAVE_RESOURCE_TYPES = {"stylesheet", "script", "image", "font"}


def local_path_for_url(url, root_netloc, out_dir):
    parsed = urlparse.urlparse(url)
    path = parsed.path.lstrip("/")
    if not path:
        path = "index.html"
    return os.path.join(out_dir, root_netloc, path)


def ensure_dir_for(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def rel_path(from_file, to_file):
    return os.path.relpath(to_file, os.path.dirname(from_file)).replace(os.sep, "/")


def rewrite_css_urls(css_local_path, css_remote_url, saved, out_dir):
    try:
        with open(css_local_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        return
    changed = False
    for ref in re.findall(r"url\(([^)]+)\)", text):
        clean = ref.strip("'\" ")
        if clean.startswith("data:"):
            continue
        abs_url = urlparse.urljoin(css_remote_url, clean)
        if abs_url in saved:
            text = text.replace(ref, rel_path(css_local_path, saved[abs_url]))
            changed = True
    if changed:
        with open(css_local_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(text)


def save_rendered_page(page, out_dir, root_netloc, saved, filename_stem):
    """Capture the current page's HTML + screenshot, rewriting asset paths to local copies."""
    html = page.content()
    final_url = page.url

    screenshot_path = os.path.join(out_dir, root_netloc, f"{filename_stem}_screenshot.png")
    ensure_dir_for(screenshot_path)
    page.screenshot(path=screenshot_path, full_page=True)

    soup = BeautifulSoup(html, "html.parser")
    page_local_path = os.path.join(out_dir, root_netloc, f"{filename_stem}.html")

    for tag, attr in (("link", "href"), ("script", "src"), ("img", "src"), ("source", "src")):
        for el in soup.find_all(tag):
            val = el.get(attr)
            if not val or val.startswith("data:"):
                continue
            abs_url = urlparse.urljoin(final_url, val).split("#")[0]
            if abs_url in saved:
                el[attr] = rel_path(page_local_path, saved[abs_url])
                if tag == "link":
                    rewrite_css_urls(saved[abs_url], abs_url, saved, out_dir)

    ensure_dir_for(page_local_path)
    with open(page_local_path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(str(soup))

    print(f"[info] saved page: {page_local_path}")
    print(f"[info] saved screenshot: {screenshot_path}")
    return page_local_path


def capture(start_url, out_dir, login_url, user_field, pass_field, username, password, wait_ms):
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError(
            "Playwright isn't installed. Run:\n  pip install playwright\n  playwright install chromium"
        )
    root_netloc = urlparse.urlparse(start_url).netloc
    saved = {}  # remote_url -> local_path
    saved_pages = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        def on_response(response):
            try:
                if response.request.resource_type not in SAVE_RESOURCE_TYPES:
                    return
                url = response.url.split("#")[0]
                if urlparse.urlparse(url).netloc != root_netloc:
                    return
                if url in saved:
                    return
                body = response.body()
                local_path = local_path_for_url(url, root_netloc, out_dir)
                ensure_dir_for(local_path)
                with open(local_path, "wb") as f:
                    f.write(body)
                saved[url] = local_path
            except Exception:
                pass  # some responses (redirects, cached, opaque) can't be read; safe to skip

        page.on("response", on_response)

        if login_url:
            print(f"[info] opening login page: {login_url}")
            page.goto(login_url, wait_until="networkidle", timeout=30000)

            # Capture the login page itself, before submitting credentials —
            # this is a real page in the site (the login screen) and worth having.
            saved_pages.append(save_rendered_page(page, out_dir, root_netloc, saved, "login"))

            print(f"[info] filling in credentials")
            page.fill(f'[name="{user_field}"]', username)
            page.fill(f'[name="{pass_field}"]', password)
            with page.expect_navigation(timeout=30000):
                page.keyboard.press("Enter")
            print(f"[info] logged in, now at: {page.url}")

        print(f"[info] navigating to target page: {start_url}")
        page.goto(start_url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(wait_ms)  # extra buffer for slow JS-rendered widgets

        saved_pages.append(save_rendered_page(page, out_dir, root_netloc, saved, "page"))

        browser.close()

    print(f"\nDone. Captured {len(saved_pages)} page(s) and {len(saved)} asset files.")
    for p_path in saved_pages:
        print(f"  {p_path}")


def main():
    parser = argparse.ArgumentParser(description="Capture a fully-rendered page, including JS-loaded content.")
    parser.add_argument("url", help="The page to capture (after login, if applicable)")
    parser.add_argument("--out", default="./captured_site", help="Output directory")
    parser.add_argument("--login-url", help="Login page URL (omit if no login needed)")
    parser.add_argument("--login-user-field", help="name attribute of the username input")
    parser.add_argument("--login-pass-field", help="name attribute of the password input")
    parser.add_argument("--login-user", default=os.environ.get("SITE_USER"))
    parser.add_argument("--login-pass", default=os.environ.get("SITE_PASS"))
    parser.add_argument("--wait-ms", type=int, default=2000, help="Extra wait (ms) after load for slow JS content")
    args = parser.parse_args()

    if args.login_url and not (args.login_user_field and args.login_pass_field and args.login_user and args.login_pass):
        print("[error] --login-url requires --login-user-field, --login-pass-field, and SITE_USER/SITE_PASS set")
        sys.exit(1)

    if not PLAYWRIGHT_AVAILABLE:
        print("Playwright isn't installed. Run:\n  pip install playwright\n  playwright install chromium")
        sys.exit(1)

    capture(args.url, args.out, args.login_url, args.login_user_field, args.login_pass_field,
            args.login_user, args.login_pass, args.wait_ms)


if __name__ == "__main__":
    main()
