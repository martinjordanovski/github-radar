#!/usr/bin/env python3
"""Daily GitHub snapshot for the Trending GitHub repos series. Public data only, no token.

Writes snapshots/YYYY-MM-DD.json with:
  trending.{daily,weekly,monthly}: GitHub Trending (repo, stars gained in period, total, language, description)
  stars: current stargazer count for every watched repo (watchlist.txt + everything trending today + AI repos created
         in the last 18 months with 40K+ stars, from GitHub search)
Run: python3 track.py   (safe to run more than once a day; it overwrites today's file)
"""
import datetime as dt, html, json, os, re, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "trending-series-tracker"}


def get(url, accept=None):
    h = dict(UA)
    if accept: h["Accept"] = accept
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
        return r.read().decode("utf-8")


def trending(since):
    t = get(f"https://github.com/trending?since={since}")
    out = []
    for a in t.split('<article class="Box-row">')[1:]:
        m = re.search(r'<h2[^>]*>\s*<a[^>]*href="/([^"]+)"', a)
        d = re.search(r'<p class="col-9[^"]*">\s*(.*?)\s*</p>', a, re.S)
        lang = re.search(r'itemprop="programmingLanguage">([^<]+)<', a)
        tot = re.search(r'href="/[^"]+/stargazers"[^>]*>.*?</svg>\s*([\d,]+)', a, re.S)
        per = re.search(r'([\d,]+) stars (?:today|this week|this month)', a)
        out.append(dict(repo=m.group(1) if m else None,
                        desc=html.unescape(re.sub("<[^>]+>", "", d.group(1))).strip() if d else "",
                        lang=lang.group(1) if lang else None,
                        total=int(tot.group(1).replace(",", "")) if tot else None,
                        gained=int(per.group(1).replace(",", "")) if per else None))
    return out


def search(q, n=100):
    u = "https://api.github.com/search/repositories?q=" + urllib.parse.quote(q) + f"&sort=stars&order=desc&per_page={n}"
    return json.loads(get(u))["items"]


def main():
    today = dt.date.today().isoformat()
    snap = dict(date=today, fetched=dt.datetime.now().astimezone().isoformat(timespec="seconds"), trending={}, stars={}, errors=[])
    for s in ["daily", "weekly", "monthly"]:
        try: snap["trending"][s] = trending(s)
        except Exception as e: snap["errors"].append(f"trending {s}: {e}")
        time.sleep(2)
    since = (dt.date.today() - dt.timedelta(days=548)).isoformat()
    try:
        for i in search(f"created:>={since} stars:>40000"):
            snap["stars"][i["full_name"]] = dict(stars=i["stargazers_count"], created=i["created_at"][:10], lang=i.get("language"),
                                                 topics=i.get("topics", [])[:8], desc=(i.get("description") or "")[:200])
    except Exception as e: snap["errors"].append(f"search: {e}")
    watch = set()
    wl = os.path.join(HERE, "watchlist.txt")
    if os.path.exists(wl):
        watch |= {l.strip() for l in open(wl) if l.strip() and not l.startswith("#")}
    for s in snap["trending"].values():
        watch |= {r["repo"] for r in s if r["repo"]}
    for repo in sorted(watch - set(snap["stars"])):          # unauthenticated API: 60 requests/hour
        try:
            d = json.loads(get(f"https://api.github.com/repos/{repo}"))
            snap["stars"][repo] = dict(stars=d["stargazers_count"], created=d["created_at"][:10], lang=d.get("language"),
                                       topics=d.get("topics", [])[:8], desc=(d.get("description") or "")[:200])
        except Exception as e: snap["errors"].append(f"repo {repo}: {e}")
    os.makedirs(os.path.join(HERE, "snapshots"), exist_ok=True)
    path = os.path.join(HERE, "snapshots", f"{today}.json")
    json.dump(snap, open(path, "w"), indent=1, ensure_ascii=False)
    print(f"{path}: {sum(len(v) for v in snap['trending'].values())} trending rows, {len(snap['stars'])} repos, {len(snap['errors'])} errors")


if __name__ == "__main__":
    main()
