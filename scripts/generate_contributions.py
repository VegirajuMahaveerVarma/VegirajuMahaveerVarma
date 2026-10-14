#!/usr/bin/env python3
"""Generate an animated contribution matrix SVG from GitHub contribution data.

Usage:
  python scripts/generate_contributions.py            # live data (needs GITHUB_TOKEN)
  python scripts/generate_contributions.py --empty    # placeholder, no data
  python scripts/generate_contributions.py --demo     # fake data, for design testing
"""
import json, os, sys, random, urllib.request
from datetime import date

OUT = os.environ.get("OUT_FILE", "assets/contributions.svg")
LOGIN = os.environ.get("GITHUB_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "VegirajuMahaveerVarma"

QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ contributionCount date weekday } }
      }
    }
  }
}"""

def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "contrib-matrix"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], cal["weeks"]

def demo_weeks():
    random.seed(3)
    weeks, d0 = [], date(2025, 10, 19)
    from datetime import timedelta
    total = 0
    for w in range(53):
        days = []
        for wd in range(7):
            d = d0 + timedelta(days=w*7+wd)
            c = random.choice([0,0,0,1,2,3,5,8]) if w > 30 else random.choice([0,0,0,0,0,1])
            total += c
            days.append({"contributionCount": c, "date": d.isoformat(), "weekday": wd})
        weeks.append({"contributionDays": days})
    return total, weeks

def empty_weeks():
    from datetime import timedelta
    d0 = date.today() - timedelta(days=date.today().weekday()+1+52*7)
    weeks = []
    for w in range(53):
        weeks.append({"contributionDays": [
            {"contributionCount": 0, "date": (d0 + timedelta(days=w*7+wd)).isoformat(), "weekday": wd}
            for wd in range(7)]})
    return 0, weeks

COLORS = ["#0b130e", "#1a4a33", "#1f6b44", "#2f9e63", "#58c985"]

def level(c, mx):
    if c <= 0: return 0
    return max(1, min(4, -(-4*c // mx)))  # ceil(4*c/mx)

def build(total, weeks, caption=None):
    P, CELL, LEFT, TOP = 17, 13, 40, 74
    W, H = 1000, 250
    all_counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    mx = max(all_counts) if any(all_counts) else 1
    cells, months, last_m = [], [], None
    for ci, wk in enumerate(weeks):
        days = wk["contributionDays"]
        if not days: continue
        m = date.fromisoformat(days[0]["date"]).strftime("%b").upper()
        if m != last_m and ci < len(weeks) - 2:
            months.append(f'<text x="{LEFT+ci*P}" y="{TOP-10}" class="lbl">{m}</text>')
            last_m = m
        for d in days:
            lv = level(d["contributionCount"], mx)
            x, y = LEFT + ci*P, TOP + d["weekday"]*P
            delay = round(0.4 + ci*0.028 + d["weekday"]*0.012, 3)
            cls = "c hot" if lv == 4 else "c"
            style = f"animation-delay:{delay}s,{round(delay+1.2,3)}s" if lv == 4 else f"animation-delay:{delay}s"
            n = d["contributionCount"]
            cells.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{COLORS[lv]}" style="{style}"><title>{d["date"]}: {n} contribution{"s" if n != 1 else ""}</title></rect>')
    grid_h = 7*P
    day_lbls = "".join(f'<text x="{LEFT-10}" y="{TOP+i*P+10}" text-anchor="end" class="lbl">{n}</text>'
                       for i, n in [(1,"MON"),(3,"WED"),(5,"FRI")])
    legend_x = W - 250
    legend = f'<text x="{legend_x-34}" y="{TOP+grid_h+34}" class="lbl">LESS</text>' + "".join(
        f'<rect x="{legend_x+i*20}" y="{TOP+grid_h+24}" width="13" height="13" rx="3" fill="{COLORS[i]}"/>' for i in range(5)
    ) + f'<text x="{legend_x+108}" y="{TOP+grid_h+34}" class="lbl">MORE</text>'
    right = caption or f"TOTAL: {total} // LAST 12 MONTHS"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Animated conquest ledger: {total} contributions in the last year">
  <defs>
    <linearGradient id="sw" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#58c985" stop-opacity="0"/>
      <stop offset="0.85" stop-color="#58c985" stop-opacity="0.28"/>
      <stop offset="1" stop-color="#d6ffe5" stop-opacity="0.75"/>
    </linearGradient>
    <pattern id="g" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="#58c985" stroke-opacity="0.05"/></pattern>
  </defs>
  <style>
    .lbl{{font-family:'Courier New',monospace;font-size:10px;fill:#8aa597;letter-spacing:2px}}
    .ttl{{font-family:'Courier New',monospace;font-size:13px;fill:#58c985;letter-spacing:4px;font-weight:700}}
    .tot{{font-family:'Courier New',monospace;font-size:13px;fill:#d4a72c;letter-spacing:3px;font-weight:700}}
    .c{{transform-box:fill-box;transform-origin:center;animation:pop .45s ease-out both}}
    .c.hot{{animation:pop .45s ease-out both,pulse 2.6s ease-in-out infinite}}
    .sweep{{animation:sweep 6s linear 2.2s infinite backwards}}
    @keyframes pop{{from{{opacity:0;transform:scale(.2)}}to{{opacity:1;transform:scale(1)}}}}
    @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.5}}}}
    @keyframes sweep{{0%{{transform:translateX(0);opacity:0}}8%{{opacity:1}}92%{{opacity:1}}100%{{transform:translateX({53*P}px);opacity:0}}}}
  </style>
  <rect width="{W}" height="{H}" rx="10" fill="#070a08"/>
  <rect width="{W}" height="{H}" rx="10" fill="url(#g)"/>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="none" stroke="#1d4d37"/>
  <text x="40" y="34" class="ttl">CONQUEST LEDGER</text>
  <text x="{W-40}" y="34" text-anchor="end" class="tot">{right}</text>
  {"".join(months)}
  {day_lbls}
  {chr(10).join(cells)}
  <rect class="sweep" x="{LEFT-46}" y="{TOP-4}" width="46" height="{grid_h+4}" fill="url(#sw)" opacity="0" pointer-events="none"/>
  {legend}
  <g fill="none" stroke="#58c985" stroke-width="2" opacity="0.8">
    <path d="M10 28V10H28"/><path d="M972 10H990V28"/><path d="M10 222V240H28"/><path d="M990 222V240H972"/>
  </g>
</svg>
'''

def main():
    if "--demo" in sys.argv:
        total, weeks = demo_weeks(); svg = build(total, weeks)
    elif "--empty" in sys.argv:
        total, weeks = empty_weeks(); svg = build(total, weeks, "AWAITING FIRST SYNC")
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token: raise SystemExit("GITHUB_TOKEN is not set")
        total, weeks = fetch(LOGIN, token); svg = build(total, weeks)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f: f.write(svg)
    print(f"wrote {OUT} ({total} contributions)")

if __name__ == "__main__":
    main()
