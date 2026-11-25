#!/usr/bin/env python3
"""Run tracker/track.py on GitHub Actions without changing it.

- Uses the workflow's built-in GITHUB_TOKEN for api.github.com calls (higher rate limit than the
  shared, unauthenticated runner IP). It is still public data only.
- If the snapshot has errors or an empty trending list, waits two minutes and runs once more.
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tracker"))
import track  # noqa: E402

TOKEN = os.environ.get("GITHUB_TOKEN")
if TOKEN:
    _orig = track.get

    def get(url, accept=None):
        if url.startswith("https://api.github.com/"):
            h = dict(track.UA, Authorization=f"Bearer {TOKEN}")
            if accept:
                h["Accept"] = accept
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
                return r.read().decode("utf-8")
        return _orig(url, accept)

    track.get = get


def problems():
    import datetime as dt
    path = os.path.join(track.HERE, "snapshots", f"{dt.date.today().isoformat()}.json")
    if not os.path.exists(path):
        return ["no snapshot written"]
    s = json.load(open(path))
    out = list(s.get("errors", []))
    if not s.get("trending", {}).get("daily"):
        out.append("daily trending list is empty")
    return out


for attempt in (1, 2):
    try:
        track.main()
    except Exception as e:  # network error before the file was written
        print(f"attempt {attempt}: {e}")
    p = problems()
    if not p:
        break
    print(f"attempt {attempt} problems: {p[:5]}")
    if attempt == 1:
        time.sleep(120)
else:
    # Both attempts had problems. Keep a partial snapshot, but never commit an empty one:
    # remove it and fail the run so GitHub emails a failure notice.
    import datetime as dt
    path = os.path.join(track.HERE, "snapshots", f"{dt.date.today().isoformat()}.json")
    s = json.load(open(path)) if os.path.exists(path) else {}
    if not s.get("stars") and not any(s.get("trending", {}).values()):
        if os.path.exists(path):
            os.remove(path)
        sys.exit("snapshot failed twice, nothing saved")
