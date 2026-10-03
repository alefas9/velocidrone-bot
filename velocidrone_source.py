"""
velocidrone_source.py

Διαβάζει leaderboards του Velocidrone από τα CSV αρχεία που εξάγει το ίδιο το
παιχνίδι (in-game leaderboard -> Export button -> .csv).

Γιατί CSV; Είναι ο επίσημος τρόπος εξαγωγής (VelociDrone manual) και δεν χρειάζεται
login/scraping στο website. Όποιος από την ομάδα κάνει export το leaderboard ενός
track, ρίχνει το αρχείο στον φάκελο TRACKS_DIR και το bot κάνει τα υπόλοιπα.

Προσαρμογή: αν το CSV της δικής σου έκδοσης έχει διαφορετικά ονόματα στηλών,
τρέξε μία φορά:  python velocidrone_source.py --inspect path/to/file.csv
για να δεις τι ανιχνεύτηκε και πρόσθεσε τα aliases στα NAME_ALIASES / TIME_ALIASES.
"""

import csv
import os
import re
import sys


NAME_ALIASES = ["name", "pilot", "player", "user", "username", "pilot name"]
TIME_ALIASES = ["time", "lap time", "best time", "best lap", "score", "result"]


def _norm_col(col: str) -> str:
    return re.sub(r"[^a-z]", "", col.lower())


def parse_time(value: str) -> float:
    """
    Δέχεται:  "83.456" | "1:23.456" | "1:23,456" | "83,456"
    Επιστρέφει: δευτερόλεπτα (float).
    """
    v = str(value).strip().replace(",", ".")
    if ":" in v:
        minutes, _, seconds = v.rpartition(":")
        return int(minutes) * 60 + float(seconds)
    return float(v)


def _find_column(fieldnames, aliases):
    norm = {i: _norm_col(c) for i, c in enumerate(fieldnames)}
    for alias in aliases:
        a = _norm_col(alias)
        for i, n in norm.items():
            if n == a or a in n:
                return i
    return None


def parse_leaderboard_csv(path: str) -> list:
    """
    Επιστρέφει ταξινομημένη λίστα: [{"pilot": "...", "time": 83.456}, ...]
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(f, dialect)
        rows = [r for r in reader if any(c.strip() for c in r)]

    if not rows:
        return []

    # Βρες τη γραμμή-κεφαλίδα (πρώτη που περιέχει recognized όνομα στήλης)
    header_idx, name_col, time_col = None, None, None
    for i, row in enumerate(rows[:5]):
        n = _find_column(row, NAME_ALIASES)
        t = _find_column(row, TIME_ALIASES)
        if n is not None and t is not None:
            header_idx, name_col, time_col = i, n, t
            break

    if header_idx is None:
        # Fallback: υπόθεσε 2 στήλες (pilot, time)
        header_idx, name_col, time_col = 0, 0, 1

    entries = []
    for row in rows[header_idx + 1:]:
        if len(row) <= max(name_col, time_col):
            continue
        pilot = row[name_col].strip()
        raw_time = row[time_col].strip()
        if not pilot or not raw_time:
            continue
        try:
            entries.append({"pilot": pilot, "time": parse_time(raw_time)})
        except ValueError:
            continue

    entries.sort(key=lambda e: e["time"])
    return entries


def load_all_tracks(tracks_dir: str) -> dict:
    """Σαρώνει φάκελο -> {track_name: [entries...]} (track name = όνομα αρχείου χωρίς .csv)."""
    result = {}
    if not os.path.isdir(tracks_dir):
        return result
    for fname in sorted(os.listdir(tracks_dir)):
        if not fname.lower().endswith(".csv"):
            continue
        track = os.path.splitext(fname)[0].strip()
        entries = parse_leaderboard_csv(os.path.join(tracks_dir, fname))
        if entries:
            result[track] = entries
    return result


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--inspect":
        entries = parse_leaderboard_csv(sys.argv[2])
        print(f"Ανιχνεύτηκαν {len(entries)} εγγραφές:")
        for e in entries[:10]:
            print(f"  {e['pilot']:<20} {e['time']:.3f}s")
    else:
        print(__doc__)
