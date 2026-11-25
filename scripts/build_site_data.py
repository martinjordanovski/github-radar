#!/usr/bin/env python3
"""Build the small JSON files the martinjordanovski.com/trending page reads.

Reads tracker/snapshots/*.json and writes:
  data/index.json    list of snapshot dates, watchlist, last update time
  data/history.json  star count per repo per day (last 120 days) + which repos were on daily Trending each day
Run after track.py:  python3 scripts/build_site_data.py [output_dir]
"""
import glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(ROOT, "tracker", "snapshots")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data")
KEEP_DAYS = 120


def main():
    files = sorted(glob.glob(os.path.join(SNAP, "????-??-??.json")))
    if not files:
        sys.exit("no snapshots found")
    snaps = [json.load(open(f)) for f in files]
    dates = [s["date"] for s in snaps]
    recent = snaps[-KEEP_DAYS:]
    rdates = dates[-KEEP_DAYS:]

    repos = set()
    for s in recent:
        repos |= set(s["stars"])
    stars = {r: [s["stars"].get(r, {}).get("stars") for s in recent] for r in sorted(repos)}
    daily = {s["date"]: [x["repo"] for x in s["trending"].get("daily", []) if x.get("repo")] for s in snaps}

    watch = []
    wl = os.path.join(ROOT, "tracker", "watchlist.txt")
    if os.path.exists(wl):
        watch = [l.strip() for l in open(wl) if l.strip() and not l.startswith("#")]

    os.makedirs(OUT, exist_ok=True)
    index = dict(updated=snaps[-1].get("fetched"), dates=dates, watchlist=watch)
    json.dump(index, open(os.path.join(OUT, "index.json"), "w"), indent=1)
    json.dump(dict(dates=rdates, stars=stars, daily=daily), open(os.path.join(OUT, "history.json"), "w"), separators=(",", ":"))
    print(f"{OUT}: {len(dates)} snapshots, {len(stars)} repos in history")


if __name__ == "__main__":
    main()
