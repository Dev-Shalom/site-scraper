#!/usr/bin/env python3
"""
site_scraper.py — Mirror a website's pages, CSS, JS, and images for design reference.

USAGE:
    python site_scraper.py https://example.com --out ./scraped_site --max-pages 40

WHAT IT DOES:
    - Crawls internal (same-domain) pages starting from the given URL
    - Saves each page's HTML (with links rewritten to point to local copies)
    - Downloads every linked CSS file, JS file, image, and font
    - Preserves folder structure so you can open index.html locally and
      browse the site offline, inspect stylesheets, etc.

WHAT IT WON'T DO:
    - It does NOT execute JavaScript. If the target site is a heavy SPA
      (React/Vue/Next.js client-rendered), the raw HTML may be mostly empty
      <div id="root"></div>. In that case you'd need a headless-browser
      approach (Playwright/Selenium) to capture the rendered DOM instead —
      ask if you want that version.
    - It does NOT bypass or crack logins. Authenticated scraping below only
      works if you already have valid credentials/access to the site.

LOGGED-IN / GATED PAGES:
    Two ways to carry an authenticated session, pick whichever fits the site:

    1) Cookie file (recommended, works on almost any site):
       Log into the site normally in your browser, export cookies with an
       extension like "Get cookies.txt LOCALLY" (Chrome/Firefox) in
       Netscape cookie format, save as cookies.txt, then run:

           python site_scraper.py https://example.com/dashboard \\
               --out ./scraped_site --cookies cookies.txt

    2) Auto form login (simple username/password forms only):

           python site_scraper.py https://example.com/dashboard \\
               --out ./scraped_site \\
               --login-url https://example.com/login \\
               --login-user-field email --login-pass-field password \\
               --login-user "$SITE_USER" --login-pass "$SITE_PASS"

       Pass credentials via environment variables, not hardcoded in a
       script you might commit to a public repo:
           export SITE_USER="you@example.com"
           export SITE_PASS="yourpassword"

    If the site is a JS-heavy SPA where login redirects client-side, neither
    approach above will work — you'd need a headless-browser (Playwright)
    version that drives a real browser session. Ask if you need that.

ETHICAL/LEGAL NOTE:
    Only do this against sites you're authorized to access (e.g. your own
    account, or a client's staging site you've been given credentials for).
    Use it to study structure, layout, and styling patterns for building
    something new/inspired — not to republish someone else's copyrighted
    text, images, or code wholesale as your own.
"""

import argparse
import http.cookiejar
import os
import re
import sys
import time
import urllib.parse as urlparse
from collections import deque

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DesignReferenceBot/1.0; +for-client-rebuild-project)"
}

ASSET_TAGS = {
    "link": "href",      # css, favicons, preload fonts
    "script": "src",
    "img": "src",
    "source": "src",
}


def is_same_domain(url, root_netloc):
    return urlparse.urlparse(url).netloc in ("", root_netloc)


def local_path_for_url(url, root_netloc, out_dir):
    """Map a remote URL to a local file path, mirroring its path structure."""
    parsed = urlparse.urlparse(url)
    path = parsed.path
    if path == "" or path.endswith("/"):
        path += "index.html"
    # strip leading slash, sanitize
    path = path.lstrip("/")
    local = os.path.join(out_dir, parsed.netloc or root_netloc, path)
    return local


def ensure_dir_for(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def download_binary(url, dest_path, session, delay):
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        ensure_dir_for(dest_path)
        with open(dest_path, "wb") as f:
            f.write(r.content)
        time.sleep(delay)
        return True
    except Exception as e:
        print(f"  [warn] failed to fetch asset {url}: {e}")
        return False


def rewrite_and_relative(dest_page_path, asset_local_path, out_dir):
    """Return a relative path from the page to the asset, for rewriting <link>/<script>/<img> tags."""
    return os.path.relpath(asset_local_path, os.path.dirname(dest_page_path))


def extract_css_url_refs(css_text):
    """Find url(...) references inside a CSS file (for fonts/background images)."""
    return re.findall(r"url\(([^)]+)\)", css_text)


def process_css_file(css_local_path, css_remote_url, session, out_dir, root_netloc, delay):
    """Download assets referenced inside a CSS file (fonts, background images) and rewrite paths."""
    try:
        with open(css_local_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        return

    refs = extract_css_url_refs(text)
    changed = False
    for ref in refs:
        clean = ref.strip("'\" ")
        if clean.startswith("data:"):
            continue
        abs_url = urlparse.urljoin(css_remote_url, clean)
        if not is_same_domain(abs_url, root_netloc):
            continue
        asset_local = local_path_for_url(abs_url, root_netloc, out_dir)
        if download_binary(abs_url, asset_local, session, delay):
            rel = rewrite_and_relative(css_local_path, asset_local, out_dir)
            text = text.replace(ref, rel)
            changed = True

    if changed:
        with open(css_local_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(text)


def load_cookies(session, cookie_file):
    """Load a Netscape-format cookies.txt (e.g. from 'Get cookies.txt LOCALLY' extension)."""
    jar = http.cookiejar.MozillaCookieJar(cookie_file)
    try:
        jar.load(ignore_discard=True, ignore_expires=True)
    except Exception as e:
        print(f"[error] could not read cookie file '{cookie_file}': {e}")
        sys.exit(1)
    session.cookies = jar
    print(f"[info] loaded {len(jar)} cookies from {cookie_file}")


def form_login(session, login_url, user_field, pass_field, username, password):
    """Fetch the login page, find the form, submit it with credentials, keep the resulting session."""
    print(f"[info] fetching login page: {login_url}")
    resp = session.get(login_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    form = soup.find("form")
    if not form:
        print("[error] no <form> found on login page — this site likely needs a headless-browser approach instead.")
        sys.exit(1)

    action = form.get("action") or login_url
    post_url = urlparse.urljoin(login_url, action)

    # Collect all existing fields (hidden CSRF tokens etc.) then overlay credentials
    payload = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        if name:
            payload[name] = inp.get("value", "")
    payload[user_field] = username
    payload[pass_field] = password

    print(f"[info] submitting login form to: {post_url}")
    login_resp = session.post(post_url, data=payload, headers=HEADERS, timeout=15)
    login_resp.raise_for_status()
    print(f"[info] login submitted (status {login_resp.status_code}) — proceeding to crawl as this session")


def scrape_site(start_url, out_dir, max_pages, delay, cookie_file=None, login_cfg=None):
    root_netloc = urlparse.urlparse(start_url).netloc
    session = requests.Session()

    if cookie_file:
        load_cookies(session, cookie_file)
    elif login_cfg:
        form_login(session, **login_cfg)

    visited = set()
    queue = deque([start_url])
    page_count = 0

    while queue and page_count < max_pages:
        url = queue.popleft()
        url = url.split("#")[0]  # drop fragments
        if url in visited:
            continue
        visited.add(url)

        print(f"[{page_count + 1}/{max_pages}] Fetching page: {url}")
        try:
            resp = session.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"  [warn] failed to fetch page {url}: {e}")
            continue

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        page_local_path = local_path_for_url(url, root_netloc, out_dir)

        # --- Handle assets (css, js, img, source) ---
        for tag_name, attr in ASSET_TAGS.items():
            for tag in soup.find_all(tag_name):
                src = tag.get(attr)
                if not src or src.startswith("data:"):
                    continue
                abs_url = urlparse.urljoin(url, src)
                if not is_same_domain(abs_url, root_netloc):
                    continue
                asset_local = local_path_for_url(abs_url, root_netloc, out_dir)
                if download_binary(abs_url, asset_local, session, delay):
                    if tag_name == "link" and "stylesheet" in (tag.get("rel") or []):
                        process_css_file(asset_local, abs_url, session, out_dir, root_netloc, delay)
                    rel = rewrite_and_relative(page_local_path, asset_local, out_dir)
                    tag[attr] = rel

        # --- Handle inline <style> url() refs (rare but happens) ---
        # (kept simple; most sites use external CSS)

        # --- Find internal links to crawl further ---
        for a in soup.find_all("a", href=True):
            abs_link = urlparse.urljoin(url, a["href"]).split("#")[0]
            if is_same_domain(abs_link, root_netloc) and abs_link not in visited:
                queue.append(abs_link)
            # Rewrite internal links to local relative paths too
            if is_same_domain(abs_link, root_netloc):
                target_local = local_path_for_url(abs_link, root_netloc, out_dir)
                a["href"] = rewrite_and_relative(page_local_path, target_local, out_dir)

        ensure_dir_for(page_local_path)
        with open(page_local_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(str(soup))

        page_count += 1
        time.sleep(delay)

    print(f"\nDone. Saved {page_count} pages to: {out_dir}")
    print(f"Open {os.path.join(out_dir, root_netloc, 'index.html')} in a browser to browse offline.")


def main():
    parser = argparse.ArgumentParser(description="Mirror a website for design/reference purposes.")
    parser.add_argument("url", help="Starting URL of the site to scrape")
    parser.add_argument("--out", default="./scraped_site", help="Output directory")
    parser.add_argument("--max-pages", type=int, default=30, help="Max number of pages to crawl")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay in seconds between requests (be polite)")
    parser.add_argument("--cookies", help="Path to a Netscape-format cookies.txt exported from your browser")
    parser.add_argument("--login-url", help="URL of the login page (for auto form-login)")
    parser.add_argument("--login-user-field", help="Name attribute of the username/email input field")
    parser.add_argument("--login-pass-field", help="Name attribute of the password input field")
    parser.add_argument("--login-user", default=os.environ.get("SITE_USER"),
                         help="Username/email (defaults to SITE_USER env var)")
    parser.add_argument("--login-pass", default=os.environ.get("SITE_PASS"),
                         help="Password (defaults to SITE_PASS env var — avoid passing on the CLI directly)")
    args = parser.parse_args()

    login_cfg = None
    if args.login_url:
        missing = [n for n, v in [
            ("--login-user-field", args.login_user_field),
            ("--login-pass-field", args.login_pass_field),
            ("--login-user (or SITE_USER env var)", args.login_user),
            ("--login-pass (or SITE_PASS env var)", args.login_pass),
        ] if not v]
        if missing:
            print(f"[error] --login-url requires: {', '.join(missing)}")
            sys.exit(1)
        login_cfg = {
            "login_url": args.login_url,
            "user_field": args.login_user_field,
            "pass_field": args.login_pass_field,
            "username": args.login_user,
            "password": args.login_pass,
        }

    scrape_site(args.url, args.out, args.max_pages, args.delay,
                cookie_file=args.cookies, login_cfg=login_cfg)


if __name__ == "__main__":
    main()
