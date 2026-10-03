"""
velocidrone_web.py

ΑΥΤΟΜΑΤΗ πηγή δεδομένων - polling του velocidrone.com ΧΩΡΙΣ login και ΧΩΡΙΣ
χειροκίνητα exports. Οι πιλότοι απλώς ανεβάζουν τους χρόνους τους in-game
(setting "Auto Leaderboard Upload: Yes" - Options/Main Settings) και το bot
τα μαζεύει μόνο του.

Ροή:
  admin εντολή:  python admin.py week "Ονομα Πιστας" "https://...leaderboard..."
  bot polling:   python update_leaderboard.py --loop 300 --source web
  -> κατεβάζει το leaderboard, χωρίζει 5inch/whoop με βάση το μοντέλο quad,
     ποστάρει βελτιώσεις + teasers + duels στο Discord.

Αν το site αλλάξει μορφή:  python velocidrone_web.py --probe <URL>
"""
from __future__ import annotations

import json
import os
import re
import time

import requests

from config import WEB_DELAY, WEB_PAGES, WEB_VERSION, REQUEST_TIMEOUT, WEEKLY_TRACK_FILE
from velocidrone_source import parse_time

BASE = "https://www.velocidrone.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

_session = requests.Session()
_session.headers.update(HEADERS)

NAME_ALIASES = ["name", "pilot", "player", "username"]
TIME_ALIASES = ["time", "lap", "best", "result", "score"]
MODEL_ALIASES = ["model", "quad", "drone", "aircraft"]

# Χάρτης μοντέλων -> κλάση. Πρόσθεσε/διόρθωσε ό,τι χρησιμοποιεί η ομάδα σου.
# Το bot κάνει case-insensitive substring match: αν το μοντέλο ΠΕΡΙΕΧΕΙ το
# κλειδί, ανήκει στην κλάση. Ό,τι δεν ταιριάζει -> "other".
CLASS_MAP = {
    "5inch": ["tbs", "five33", "5 inch", '5"', "astrox", "drl racer", "spec"],
    "whoop": ["newbeedrone", "tinyhawk", "whoop", "mobula", "meteor", "micro"],
}
CLASS_LABELS = {"5inch": "🏁 5 Inch", "whoop": "🐝 Whoop", "other": "🛠️ Άλλο"}


def classify_model(model: str) -> str:
    m = (model or "").lower()
    for cls, keys in CLASS_MAP.items():
        for k in keys:
            if k in m:
                return cls
    return "other"


def split_by_class(entries: list) -> dict:
    """{class: [entries...]} - κάθε κλάση με το δικό της ταξινομημένο leaderboard."""
    classes = {}
    for e in entries:
        classes.setdefault(e.get("class", "other"), []).append(e)
    for lst in classes.values():
        lst.sort(key=lambda x: x["time"])
    return classes


# ---------------------------------------------------------------- fetch

def _get(url: str) -> requests.Response:
    r = _session.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    time.sleep(WEB_DELAY)  # ευγενικό polling
    return r


# ---------------------------------------------------------------- parse

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _find_col(headers: list, aliases: list):
    norm = [_norm(h) for h in headers]
    for a in aliases:
        na = _norm(a)
        for i, n in enumerate(norm):
            if n and (n == na or na in n):
                return i
    return None


def _clean(cell: str) -> str:
    return re.sub(r"<[^>]+>", "", str(cell)).strip()


def _rows_to_entries(rows, name_col, time_col, model_col=None):
    entries = []
    for row in rows:
        if len(row) <= max(name_col, time_col):
            continue
        pilot = _clean(row[name_col])
        raw = _clean(row[time_col])
        if not pilot or not raw:
            continue
        try:
            e = {"pilot": pilot, "time": parse_time(raw)}
        except ValueError:
            continue
        if model_col is not None and len(row) > model_col:
            e["model"] = _clean(row[model_col])
            e["class"] = classify_model(e["model"])
        entries.append(e)
    entries.sort(key=lambda e: e["time"])
    return entries


def _parse_table(html: str) -> list:
    m = re.search(r"<table[^>]*>(.*?)</table>", html, re.S | re.I)
    if not m:
        return []
    table = m.group(1)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S | re.I)
    body_rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S | re.I) for r in rows]
    body_rows = [r for r in body_rows if r]
    if not body_rows:
        return []

    # Αν υπάρχει <thead>, εκεί είναι τα headers
    thead = re.search(r"<thead[^>]*>(.*?)</thead>", table, re.S | re.I)
    if thead:
        header_cells = [_clean(c) for c in re.findall(
            r"<t[hd][^>]*>(.*?)</t[hd]>", thead.group(1), re.S | re.I)]
        data_rows = body_rows
    else:
        # Χωρίς thead: η 1η γραμμή ΜΠΟΡΕΙ να είναι header - έλεγξέ το
        candidate = [_clean(c) for c in body_rows[0]]
        n_col = _find_col(candidate, NAME_ALIASES)
        t_col = _find_col(candidate, TIME_ALIASES)
        if (n_col is not None and t_col is not None and len(body_rows) > 1
                and len(body_rows[1]) == len(candidate)):
            header_cells, data_rows = candidate, body_rows[1:]
        else:
            header_cells, data_rows = [], body_rows  # όλα data (κλασικό format)

    if header_cells:
        name_col = _find_col(header_cells, NAME_ALIASES)
        time_col = _find_col(header_cells, TIME_ALIASES)
        model_col = _find_col(header_cells, MODEL_ALIASES)
        if name_col is not None and time_col is not None and data_rows \
                and len(data_rows[0]) == len(header_cells):
            return _rows_to_entries(data_rows, name_col, time_col, model_col)

    if data_rows and len(data_rows[0]) >= 3:
        # κλασικό Velocidrone format: θέση, χρόνος, όνομα, χώρα, ranking, model
        model_col = 5 if len(data_rows[0]) > 5 else None
        return _rows_to_entries(data_rows, 2, 1, model_col)
    return []


def _parse_embedded_json(html: str) -> list:
    entries = []
    for m in re.finditer(r"<script[^>]*>(.*?)</script>", html, re.S | re.I):
        txt = m.group(1)
        if '"time"' not in txt and '"name"' not in txt:
            continue
        for mm in re.finditer(
                r'"name"\s*:\s*"([^"]+)"\s*,\s*"time"\s*:\s*"?([\d:.]+)"?(?:\s*,\s*"model"\s*:\s*"([^"]*)")?', txt):
            try:
                e = {"pilot": mm.group(1), "time": parse_time(mm.group(2))}
            except ValueError:
                continue
            if mm.group(3):
                e["model"] = mm.group(3)
                e["class"] = classify_model(e["model"])
            entries.append(e)
    entries.sort(key=lambda e: e["time"])
    seen, out = set(), []
    for e in entries:
        if e["pilot"] not in seen:
            seen.add(e["pilot"])
            out.append(e)
    return out


def parse_leaderboard_html(html: str) -> list:
    entries = _parse_table(html)
    if entries:
        return entries
    return _parse_embedded_json(html)


# ---------------------------------------------------------------- public API

def fetch_track(track_name: str, url: str, pages: int = WEB_PAGES) -> list:
    all_entries = []
    for page in range(1, pages + 1):
        page_url = url if page == 1 else f"{url}{'&' if '?' in url else '?'}page={page}"
        try:
            html = _get(page_url).text
        except requests.RequestException as e:
            print(f"  ! σφάλμα fetch {page_url}: {e}")
            break
        entries = parse_leaderboard_html(html)
        if not entries:
            if page == 1:
                print(f"  ! δεν βρέθηκαν εγγραφές στο {url} - δοκίμασε --probe")
            break
        all_entries.extend(entries)
    best = {}
    for e in all_entries:
        if e["pilot"] not in best or e["time"] < best[e["pilot"]]["time"]:
            best[e["pilot"]] = e
    return sorted(best.values(), key=lambda e: e["time"])


def get_weekly_track() -> dict | None:
    """Τι έχει ορίσει ο admin ως πίστα της εβδομάδας (weekly_track.json)."""
    if not os.path.exists(WEEKLY_TRACK_FILE):
        return None
    with open(WEEKLY_TRACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_tracks_web() -> dict:
    """Κύρια συνάρτηση -> {track_name: [entries...]}."""
    weekly = get_weekly_track()
    if weekly:
        entries = fetch_track(weekly["track"], weekly["url"])
        return {weekly["track"]: entries} if entries else {}
    print("  ! Δεν έχει οριστεί πίστα εβδομάδας. Ο admin τρέχει:")
    print('    python admin.py week "Ονομα Πιστας" "https://www.velocidrone.com/leaderboard/..."')
    return {}


# ---------------------------------------------------------------- probe

def probe(url: str) -> None:
    html = _get(url).text
    print(f"URL: {url}")
    print(f"Μέγεθος HTML: {len(html)} chars | <table>: {'<table' in html.lower()} | "
          f"track-grid: {'track-grid' in html}")
    entries = parse_leaderboard_html(html)
    print(f"Εγγραφές που παρσάρονται: {len(entries)}")
    for e in entries[:10]:
        model = e.get("model", "-")
        cls = e.get("class", "-")
        print(f"  {e['pilot']:<22} {e['time']:>9.3f}s  {model:<18} -> {cls}")
    if not entries:
        print("Ξεκίνημα HTML:", re.sub(r"\s+", " ", html[:400]))


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "--probe":
        probe(sys.argv[2])
    else:
        for t, es in load_all_tracks_web().items():
            print(f"«{t}» -> {len(es)} πιλότοι, κορυφή: {es[0]['pilot']} {es[0]['time']:.3f}s")
