# Site Scraper Toolkit

```
 ____ ___ _____ _____   ____   ____ ____      _    ____  _____ ____
/ ___|_ _|_   _| ____| / ___| / ___|  _ \    / \  |  _ \| ____|  _ \
\___ \| |  | | |  _|   \___ \| |   | |_) |  / _ \ | |_) |  _| | |_) |
 ___) | |  | | | |___   ___) | |___|  _ <  / ___ \|  __/| |___|  _ <
|____/___| |_| |_____| |____/ \____|_| \_\/_/   \_\_|   |_____|_| \_\
```

Copy a site's pages, styling, and structure for design reference — so you can rebuild or customize it to match a client's brief.

Two scraping modes, one interactive menu. No flags to memorize.

---

## Quick Start

```bash
pip install -r requirements.txt
python -m playwright install chromium
python scrape.py
```

That's three commands, run once. After that, just `python scrape.py` every time.

> **Why two install steps?** `pip install -r requirements.txt` installs the Python packages. Playwright *also* needs an actual browser binary (headless Chromium) — that's a separate ~150MB download the second command handles. This only needs to be done once.

---

## What's Included

```
site-scraper/
├── scrape.py               <- START HERE. Interactive menu.
├── site_scraper.py         <- Quick Scrape engine
├── full_page_capture.py    <- Full Page Capture engine
├── requirements.txt
└── .gitignore
```

Run `python scrape.py` and pick a mode:

| Mode | Use it for |
|---|---|
| **[1] Quick Scrape** | Regular multi-page sites — blogs, business sites, portfolios. Fast, no browser needed. |
| **[2] Full Page Capture** | JS-driven pages, dashboards, dynamic content. Renders the page in a real headless browser and also saves a screenshot. |

Not sure which one? Start with Quick Scrape. If the result looks incomplete compared to what you see in your actual browser, use Full Page Capture instead.

---

## Scraping a Page Behind a Login

Both modes support it. When `scrape.py` asks, you'll need:

1. **The login page URL**
2. **The field names** on that login form — not your credentials, the technical `name="..."` attribute in the HTML. Find these by right-clicking the username box on the login page → **Inspect**.
3. **Your actual username and password** — entered securely, hidden as you type, never written to disk.

> **Use responsibly.** Only scrape sites/accounts you're authorized to access. This tool is for studying layout and structure to build something new — not for republishing someone else's content or private data as your own.

---

## Troubleshooting

**`playwright : command not recognized` (Windows)**
pip installed it, but it's not on your PATH. Run it through Python instead:
```powershell
python -m playwright install chromium
```

**`Executable doesn't exist at ...chrome-headless-shell.exe`**
The browser binary didn't fully download. Re-run:
```powershell
python -m playwright install chromium
```

**`ModuleNotFoundError: No module named 'requests'` (or similar)**
Dependencies aren't installed yet:
```powershell
pip install -r requirements.txt
```

**PowerShell doesn't like my multi-line command / `\` line breaks**
PowerShell uses a backtick `` ` `` for line continuation, not `\`. Easiest fix: just put the whole command on one line.

---

## Output

Results land in `./scraped_site/` (Quick Scrape) or `./captured_site/` (Full Page Capture), mirroring the site's folder structure. Open the saved HTML file in a browser to view it offline.

These folders are git-ignored by default — they're local working copies, not meant to be committed.
