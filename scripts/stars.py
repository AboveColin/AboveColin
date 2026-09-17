#!/usr/bin/env python3
"""Build the star history for AboveColin and render it into the profile README.

Two modes, because GitHub guards the two data sources differently.

  python3 scripts/stars.py
      Snapshot. Reads the current star count per repository from
      /users/AboveColin/repos, which answers without a token, and appends today
      to the series already in data/stars.json. This is what the daily workflow
      runs.

  GITHUB_TOKEN=$(gh auth token) python3 scripts/stars.py --backfill
      Rebuild. Reads every star event (repo, starred_at) and reconstructs the
      whole series from scratch. /repos/{owner}/{repo}/stargazers answers 401
      without a token and 403 "Resource not accessible by integration" for the
      Actions GITHUB_TOKEN, which is scoped to this repository only, so this
      mode runs from a laptop with a personal token.

Both modes write data/stars.json, render assets/stars-{light,dark}.svg and
replace the generated block in README.md.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

USER = "AboveColin"
ROOT = Path(__file__).resolve().parent.parent
RAW = f"https://raw.githubusercontent.com/{USER}/{USER}/main"
API = "https://api.github.com"

# dataviz slot 1 (blue), validated against the GitHub README surfaces:
# light #2a78d6 on #ffffff and dark #3987e5 on #0d1117 both pass >= 3:1.
THEMES = {
    "light": {
        "surface": "#ffffff",
        "accent": "#2a78d6",
        "ink": "#1f2328",
        "muted": "#59636e",
        "grid": "#e6e8eb",
        "axis": "#d0d7de",
    },
    "dark": {
        "surface": "#0d1117",
        "accent": "#3987e5",
        "ink": "#e6edf3",
        "muted": "#9198a1",
        "grid": "#21262d",
        "axis": "#30363d",
    },
}

W, H = 880, 280
PAD_L, PAD_R, PAD_T, PAD_B = 48, 52, 48, 34
PLOT_W = W - PAD_L - PAD_R
PLOT_H = H - PAD_T - PAD_B

FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"


class RateLimited(Exception):
    """GitHub answered 403 with no requests left in the window."""


def request(url: str, accept: str, token: str | None) -> tuple[object, dict]:
    req = urllib.request.Request(url, headers={
        "Accept": accept,
        "User-Agent": f"{USER}-profile-stars",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp), dict(resp.headers)


def get(url: str, accept: str = "application/vnd.github+json") -> tuple[object, dict]:
    """Read one page, with an anonymous retry and one rate-limit retry.

    The Actions GITHUB_TOKEN is scoped to this repository, so listing the
    stargazers of any other repository answers 403 "Resource not accessible by
    integration". Star data on a public repository is readable without a token,
    so that is the fallback. Anonymous requests get 60 per hour per IP, hence
    the single sleep-and-retry before giving up.
    """
    token = os.environ.get("STARS_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    attempts: list[str | None] = [token, None] if token else [None]
    last: urllib.error.HTTPError | None = None
    for waited in (False, True):
        for attempt_token in attempts:
            try:
                return request(url, accept, attempt_token)
            except urllib.error.HTTPError as err:
                last = err
                remaining = err.headers.get("x-ratelimit-remaining")
                if err.code == 403 and remaining == "0":
                    break  # No point trying the other identity on this url.
                if err.code not in (401, 403, 404):
                    raise SystemExit(
                        f"GitHub API {err.code} on {url}: "
                        f"{err.read().decode('utf-8', 'replace')[:400]}"
                    ) from err
        if waited:
            break
        if last is not None and last.code == 403 and last.headers.get("x-ratelimit-remaining") == "0":
            print("rate limited, waiting 65s", file=sys.stderr)
            time.sleep(65)
        else:
            break
    assert last is not None
    if last.code == 403 and last.headers.get("x-ratelimit-remaining") == "0":
        raise RateLimited(url)
    raise SystemExit(
        f"GitHub API {last.code} on {url}: "
        f"{last.read().decode('utf-8', 'replace')[:400]}"
    )


def paged(url: str, accept: str = "application/vnd.github+json") -> list:
    out: list = []
    page = 1
    while True:
        sep = "&" if "?" in url else "?"
        data, _ = get(f"{url}{sep}per_page=100&page={page}", accept)
        if not data:
            break
        out.extend(data)
        if len(data) < 100:
            break
        page += 1
        if page > 20:
            break
    return out


def read_repos() -> tuple[list, dict[str, dict]]:
    repos = [r for r in paged(f"{API}/users/{USER}/repos?type=owner") if not r["fork"]]
    counted = {
        r["name"]: {
            "stars": r["stargazers_count"],
            "description": (r["description"] or "").strip(),
            "language": r["language"],
            "archived": r["archived"],
        }
        for r in repos
        if r["stargazers_count"] > 0
    }
    return repos, counted


def snapshot(previous: dict) -> dict:
    """Extend yesterday's series with today's totals."""
    repos, counted = read_repos()
    total = sum(m["stars"] for m in counted.values())
    series = [tuple(p) for p in previous.get("series", [])]
    today = date.today().isoformat()
    if series and series[-1][0] == today:
        series[-1] = (today, total)
    elif not series or series[-1][1] != total:
        series.append((today, total))
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "user": USER,
        "public_repos_own": len(repos),
        "total_stars": total,
        "repos": counted,
        "series": [list(p) for p in series],
    }


def backfill() -> dict:
    repos, counted = read_repos()
    events: list[tuple[str, str]] = []
    for name in counted:
        stargazers = paged(
            f"{API}/repos/{USER}/{name}/stargazers",
            "application/vnd.github.star+json",
        )
        for s in stargazers:
            events.append((s["starred_at"], name))
    events.sort()

    # One cumulative point per day that gained a star.
    series: list[tuple[str, int]] = []
    running = 0
    for stamp, _repo in events:
        day = stamp[:10]
        running += 1
        if series and series[-1][0] == day:
            series[-1] = (day, running)
        else:
            series.append((day, running))

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "user": USER,
        "public_repos_own": len(repos),
        "total_stars": running,
        "repos": counted,
        "series": [list(p) for p in series],
    }


def nice_step(top: float, target: int = 4) -> float:
    if top <= 0:
        return 1.0
    raw = top / target
    mag = 10 ** int(f"{raw:e}".split("e")[1])
    for mult in (1, 2, 2.5, 5, 10):
        if mag * mult >= raw:
            return mag * mult
    return mag * 10


def render(payload: dict, theme_name: str) -> str:
    t = THEMES[theme_name]
    series = [(date.fromisoformat(d), v) for d, v in payload["series"]]
    if not series:
        series = [(date.today(), 0)]
    first = series[0][0]
    last = date.today()
    span = max((last - first).days, 1)
    top = payload["total_stars"]
    step = nice_step(top)
    y_max = max(step * 1.0, (int(top / step) + 1) * step)

    def x_of(d: date) -> float:
        return PAD_L + (d - first).days / span * PLOT_W

    def y_of(v: float) -> float:
        return PAD_T + PLOT_H - (v / y_max) * PLOT_H

    # Step-after path: a star count holds until the next star arrives.
    pts: list[str] = [f"M {x_of(first):.1f} {y_of(0):.1f}"]
    prev = 0
    for d, v in series:
        pts.append(f"L {x_of(d):.1f} {y_of(prev):.1f}")
        pts.append(f"L {x_of(d):.1f} {y_of(v):.1f}")
        prev = v
    pts.append(f"L {x_of(last):.1f} {y_of(prev):.1f}")
    line = " ".join(pts)
    area = f"{line} L {x_of(last):.1f} {y_of(0):.1f} L {x_of(first):.1f} {y_of(0):.1f} Z"

    grid = []
    v = 0.0
    while v <= y_max + 1e-9:
        y = y_of(v)
        grid.append(
            f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{PAD_L + PLOT_W}" y2="{y:.1f}" '
            f'stroke="{t["axis"] if v == 0 else t["grid"]}" stroke-width="1"/>'
            f'<text x="{PAD_L - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="11" '
            f'fill="{t["muted"]}" font-family="{FONT}">{int(v)}</text>'
        )
        v += step

    ticks = []
    years = list(range(first.year, last.year + 1))
    if len(years) > 8:
        years = years[:: (len(years) // 6) or 1]
    for year in years:
        d = date(year, 1, 1)
        if d < first:
            d = first
        x = x_of(d)
        if x > PAD_L + PLOT_W - 18:
            continue
        ticks.append(
            f'<line x1="{x:.1f}" y1="{PAD_T}" x2="{x:.1f}" y2="{PAD_T + PLOT_H}" '
            f'stroke="{t["grid"]}" stroke-width="1"/>'
            f'<text x="{x:.1f}" y="{PAD_T + PLOT_H + 18}" text-anchor="middle" font-size="11" '
            f'fill="{t["muted"]}" font-family="{FONT}">{year}</text>'
        )

    # The right padding reserves room for this one direct label, so it always
    # sits beside the final point and never crosses the line.
    end_x, end_y = x_of(last), y_of(top)
    label_x = end_x + 10
    anchor = "start"
    label_y = min(max(end_y + 4, PAD_T + 8), PAD_T + PLOT_H)

    repos = payload["public_repos_own"]
    caption = (
        f'{repos} own public repositories, forks excluded. '
        f'Updated {payload["generated_at"][:10]}.'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" \
viewBox="0 0 {W} {H}" role="img" aria-label="Cumulative GitHub stars for {USER}: \
{top} stars across {repos} repositories since {first.isoformat()}.">
  <defs>
    <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{t['accent']}" stop-opacity="0.30"/>
      <stop offset="100%" stop-color="{t['accent']}" stop-opacity="0.02"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="10" fill="{t['surface']}"/>
  <text x="{PAD_L - 38}" y="26" font-size="14" font-weight="600" fill="{t['ink']}" \
font-family="{FONT}">Stars over time</text>
  <text x="{W - PAD_R}" y="26" text-anchor="end" font-size="12" fill="{t['muted']}" \
font-family="{FONT}">{caption}</text>
  {''.join(grid)}
  {''.join(ticks)}
  <path d="{area}" fill="url(#fill)"/>
  <path d="{line}" fill="none" stroke="{t['accent']}" stroke-width="2" \
stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="4.5" fill="{t['accent']}" \
stroke="{t['surface']}" stroke-width="2"/>
  <text x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="{anchor}" font-size="13" \
font-weight="600" fill="{t['ink']}" font-family="{FONT}">{top}</text>
</svg>
"""


def table(payload: dict, limit: int = 10) -> str:
    described = {k: v for k, v in payload["repos"].items() if v["description"]}
    rows = sorted(described.items(), key=lambda kv: (-kv[1]["stars"], kv[0]))[:limit]
    out = ["| Project | What it does | Stars |", "| --- | --- | --: |"]
    for name, meta in rows:
        desc = meta["description"] or ""
        if len(desc) > 96:
            desc = desc[:93].rstrip() + "..."
        desc = desc.replace("|", "\\|")
        out.append(
            f"| [{name}](https://github.com/{USER}/{name}) | {desc} | {meta['stars']} |"
        )
    return "\n".join(out)


def block(payload: dict, version: str) -> str:
    total = payload["total_stars"]
    repos = payload["public_repos_own"]
    starred = len(payload["repos"])
    return f"""<!-- stars:start -->
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="{RAW}/assets/stars-dark.svg?v={version}">
    <img alt="Cumulative GitHub stars over time: {total} stars across {starred} repositories" src="{RAW}/assets/stars-light.svg?v={version}" width="880">
  </picture>
</p>

<p align="center">
  <strong>{total}</strong> stars &middot; <strong>{repos}</strong> own public repositories &middot; <strong>{starred}</strong> of them starred by someone &middot; counted {payload['generated_at'][:10]}
</p>

### Most starred

{table(payload)}
<!-- stars:end -->"""


def main() -> int:
    store = ROOT / "data" / "stars.json"
    previous = json.loads(store.read_text()) if store.exists() else {}
    try:
        if "--backfill" in sys.argv:
            payload = backfill()
        else:
            payload = snapshot(previous)
    except RateLimited as err:
        if store.exists():
            print(f"rate limited on {err}; keeping the series from the last run",
                  file=sys.stderr)
            return 0
        print(f"rate limited on {err} and there is no earlier series to keep",
              file=sys.stderr)
        return 1
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "stars.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    version = hashlib.sha256(
        json.dumps(payload["series"]).encode()
    ).hexdigest()[:8]

    (ROOT / "assets").mkdir(exist_ok=True)
    for name in THEMES:
        (ROOT / "assets" / f"stars-{name}.svg").write_text(
            render(payload, name), encoding="utf-8"
        )

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    start, end = "<!-- stars:start -->", "<!-- stars:end -->"
    if start not in readme or end not in readme:
        print(f"README.md has no {start} ... {end} block", file=sys.stderr)
        return 1
    head = readme.split(start)[0]
    tail = readme.split(end)[1]
    readme_path.write_text(head + block(payload, version) + tail, encoding="utf-8")

    print(f"{payload['total_stars']} stars, {len(payload['series'])} points in the series, v={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
