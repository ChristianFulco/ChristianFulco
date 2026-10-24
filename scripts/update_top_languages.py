#!/usr/bin/env python3
"""Build a compact language card from public repos and the private Cérebro IA repo."""
from collections import Counter
from html import escape
import json
import os
from pathlib import Path
import urllib.request

API = "https://api.github.com"
OWNER = "ChristianFulco"
PRIVATE_REPO = "ChristianFulco/cerebro-ia"
OUTPUT = Path("assets/top-languages.svg")
COLORS = ["#3572A5", "#f1e05a", "#e34c26", "#563d7c", "#2b7489", "#4F5D95", "#00ADD8", "#89e051"]

def get_json(url, token=None):
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "ChristianFulco-language-card"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def main():
    gh_token = os.environ["GITHUB_TOKEN"]
    private_token = os.getenv("PRIVATE_REPO_TOKEN")
    totals = Counter()
    page = 1
    while True:
        repos = get_json(f"{API}/users/{OWNER}/repos?type=owner&per_page=100&page={page}", gh_token)
        for repo in repos:
            if repo.get("fork") or repo.get("archived"):
                continue
            totals.update(get_json(repo["languages_url"], gh_token))
        if len(repos) < 100:
            break
        page += 1

    private_included = False
    if private_token:
        repo = get_json(f"{API}/repos/{PRIVATE_REPO}", private_token)
        totals.update(get_json(repo["languages_url"], private_token))
        private_included = True

    entries = totals.most_common(8)
    if not entries:
        raise SystemExit("No language data found in the selected repositories.")
    total = sum(totals.values())
    bar_x, bar_y, bar_w, bar_h = 30, 94, 840, 16
    cursor = bar_x
    segments = []
    for i, (name, size) in enumerate(entries):
        segment = bar_w * size / total
        segments.append(f'<rect x="{cursor:.2f}" y="{bar_y}" width="{segment:.2f}" height="{bar_h}" fill="{COLORS[i % len(COLORS)]}"/>')
        cursor += segment

    legend = []
    for i, (name, size) in enumerate(entries):
        x, y = 30 + (i % 4) * 215, 151 + (i // 4) * 42
        legend.append(f'<circle cx="{x}" cy="{y - 5}" r="5" fill="{COLORS[i % len(COLORS)]}"/><text x="{x + 12}" y="{y}" class="label">{escape(name)} <tspan class="pct">{size * 100 / total:.1f}%</tspan></text>')

    subtitle = "Repos públicos + Cérebro IA privado" if private_included else "Repos públicos; falta configurar PRIVATE_REPO_TOKEN para incluir Cérebro IA"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="245" viewBox="0 0 900 245" role="img" aria-labelledby="title desc">
<title id="title">Linguagens mais usadas de ChristianFulco</title><desc id="desc">Distribuição das linguagens nos repositórios do GitHub.</desc>
<style>.card{{fill:#171321;stroke:#3b2b52;stroke-width:1}}.title{{font:600 22px system-ui,sans-serif;fill:#ff61d8}}.subtitle{{font:13px system-ui,sans-serif;fill:#c4b5d4}}.label{{font:14px system-ui,sans-serif;fill:#f4edf8}}.pct{{fill:#c4b5d4}}</style>
<rect class="card" x="1" y="1" width="898" height="243" rx="14"/><text id="title" x="30" y="42" class="title">Linguagens mais usadas</text><text id="desc" x="30" y="66" class="subtitle">{escape(subtitle)}</text>
<clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="8"/></clipPath><g clip-path="url(#bar)">{''.join(segments)}</g>
{''.join(legend)}</svg>
'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")

if __name__ == "__main__":
    main()
