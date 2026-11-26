# github-radar

Daily snapshot of GitHub Trending (daily, weekly, monthly) plus star counts for a watchlist, everything trending, and repos under 18 months old with 40K+ stars. Public GitHub data only.

It powers **https://martinjordanovski.com/github-trending/**: the page reads `data/` and `tracker/snapshots/` straight from this repo, so the website never needs a redeploy for new data.

## How it runs

`.github/workflows/daily-snapshot.yml` runs every day at 19:37 UTC (and from the "Run workflow" button):

1. `scripts/run_ci.py` runs `tracker/track.py` unchanged, using the workflow's built-in `GITHUB_TOKEN` for API calls. If anything fails, it waits two minutes and tries once more.
2. `scripts/build_site_data.py` writes `data/index.json` (dates, watchlist) and `data/history.json` (stars per repo per day, last 120 days).
3. The new files are committed to `main`.

## Files

| Path | What it is |
| --- | --- |
| `tracker/track.py` | the snapshot script |
| `tracker/watchlist.txt` | repos to follow every day, one `owner/name` per line |
| `tracker/snapshots/YYYY-MM-DD.json` | one snapshot per day |
| `data/index.json`, `data/history.json` | small files the web page reads |

To add a repo to the watchlist, edit `tracker/watchlist.txt` on GitHub and commit.
