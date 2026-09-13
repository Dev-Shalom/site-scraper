# Site Scraper Toolkit

Grab a website's pages, styling, and structure for design reference — so you can rebuild or customize it to match a client's brief.

Comes in two modes: a fast scraper for ordinary multi-page sites, and a browser-driven capture tool for JavaScript-heavy pages. An interactive launcher walks you through picking the right one — no command-line flags to memorize.

## Quick start

```bash
pip install -r requirements.txt
python scrape.py
```

That's it. `scrape.py` asks you a few plain-English questions (which mode you want, the URL, whether it needs a login) and takes care of the rest.

## What's included

| File | What it does |
|---|---|
| `scrape.py` | **Start here.** Interactive menu — pick a mode, answer a few questions, done. |
| `site_scraper.py` | Fast scraper for regular sites. Follows internal links across pages, downloads HTML/CSS/JS/images/fonts. |
| `full_page_capture.py` | Uses a real headless browser to load a page, run its JavaScript, and capture exactly what ends up on screen — including dynamically-loaded content. Also saves a full-page screenshot. |

## Which mode do I need?

**Quick Scrape** — for most websites: blogs, business sites, portfolios, traditional multi-page sites where the HTML you get back from the server already contains the content.

**Full Page Capture** — for single-page apps, dashboards, or any page where Quick Scrape seems to be missing content. If a page builds part of itself with JavaScript *after* it loads (filtered lists, widgets, lazy content), this mode renders it in a real browser first so nothing gets missed.

Not sure? Start with Quick Scrape — if the result looks incomplete compared to what you see in your actual browser, switch to Full Page Capture.

## Setup

```bash
pip install -r requirements.txt
```

Full Page Capture also needs a headless browser binary, installed once:

```bash
playwright install chromium
```

## Scraping a page behind a login

Both modes support logging in first. The interactive launcher will ask:

- The login page's URL
- The `name` attribute of the username and password fields (find these by right-clicking the fields on the login page → **Inspect**, and looking for `<input name="...">`)
- Your username and password (entered securely — hidden as you type, never saved to disk or shown on screen)

> **Use responsibly.** Only scrape sites/accounts you're authorized to access — your own site, a client's staging environment, or an account where you have explicit permission. This tool is meant for studying layout and structure to build something new, not for republishing someone else's content, private data, or licensed material as your own.

## Manual / advanced usage

Both tools also work directly from the command line if you'd rather skip the interactive menu — run `python site_scraper.py --help` or `python full_page_capture.py --help` for the full list of flags.

## Output

Scraped files land in `./scraped_site/` (Quick Scrape) or `./captured_site/` (Full Page Capture), mirroring the site's folder structure. Open the saved HTML file in a browser to view the result offline.

These output folders are git-ignored by default — they're meant to be local working copies, not something you'd commit to the repo.
