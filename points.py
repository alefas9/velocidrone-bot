"""
points.py

Αυτόματη βαθμολογία σεζόν για εβδομαδιαίους αγώνες.

Πότε απονέμονται πόντοι: όταν ο admin αλλάζει πίστα (admin.py week ...),
το bot κλείνει αυτόματα την προηγούμενη εβδομάδα:
  - παίρνει τους καλύτερους χρόνους κάθε πιλότου ανά κλάση (από το state.json)
  - απονέμει πόντους σύμφωνα με τον POINTS_TABLE (προεπιλογή F1-style)
  - ποστάρει αποτελέσματα + βαθμολογία σεζόν

Προαιρετικά στο .env:
  POINTS_TABLE=25,18,15,12,10,8,6,4,2,1

Διαχείριση:
  python3 admin.py standings          # τρέχουσα βαθμολογία -> Discord
  python3 admin.py award              # απονομή τώρα (χωρίς αλλαγή πίστας)
  python3 admin.py standings-reset    # μηδενισμός σεζόν (νέα σεζόν)
"""

import json
import os
from datetime import datetime

from config import STATE_FILE  # noqa: F401  (το state το περνάει ο caller)

STANDINGS_FILE = os.environ.get("STANDINGS_FILE", "standings.json")

DEFAULT_TABLE = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


def points_table() -> list:
    raw = os.environ.get("POINTS_TABLE", "")
    if raw.strip():
        try:
            return [int(x) for x in raw.split(",") if x.strip()]
        except ValueError:
            pass
    return DEFAULT_TABLE


def load_standings() -> dict:
    if not os.path.exists(STANDINGS_FILE):
        return {"classes": {}, "history": [], "awarded": []}
    try:
        with open(STANDINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"classes": {}, "history": [], "awarded": []}
    data.setdefault("classes", {})
    data.setdefault("history", [])
    data.setdefault("awarded", [])
    return data


def save_standings(data: dict) -> None:
    # atomic write: ποτέ half-written file
    tmp = STANDINGS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STANDINGS_FILE)


def final_standings_for_track(state: dict, track: str) -> dict:
    """{class: [(pilot, best_time)]} ταξινομημένα - καλύτερος χρόνος ανά πιλότο/κλάση."""
    result = {}
    for cls, entries in state.get("tracks", {}).get(track, {}).items():
        best = {}
        for key, t in entries.items():
            pilot = key.split("|")[0]
            if pilot not in best or t < best[pilot]:
                best[pilot] = t
        result[cls] = sorted(best.items(), key=lambda kv: kv[1])
    return result


def award_week(track: str, state: dict, force: bool = False) -> list:
    """Απονομή πόντων για μια ολοκληρωμένη εβδομάδα.

    IDEMPOTENT: αν η πίστα έχει ήδη απονεμηθεί, επιστρέφει [] χωρίς να δώσει
    ξανά πόντους (προστασία από διπλό admin.py week / award). Με force=True
    παρακάμπτεται ο έλεγχος (π.χ. --force-award αν ξέρεις τι κάνεις).

    Επιστρέφει λίστα από dicts: {class, results: [(pilot,time,points,medal)], season: [...]}
    """
    table = points_table()
    standings = load_standings()
    if not force and track in standings.get("awarded", []):
        print(f"Η «{track}» έχει ήδη απονεμηθεί - παράλειψη (χρησιμοποίησε --force-award για επανάληψη).")
        return []
    final = final_standings_for_track(state, track)
    out = []
    now = datetime.now().isoformat()

    for cls, ranked in final.items():
        if not ranked:
            continue
        cls_key = cls or "other"
        cst = standings["classes"].setdefault(cls_key, {})
        results = []
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        for pos, (pilot, t) in enumerate(ranked):
            pts = table[pos] if pos < len(table) else 0
            p = cst.setdefault(pilot, {"points": 0, "wins": 0, "podiums": 0,
                                       "races": 0, "best": None})
            p["points"] += pts
            p["races"] += 1
            if pos == 0:
                p["wins"] += 1
            if pos < 3:
                p["podiums"] += 1
            if p["best"] is None or t < p["best"]:
                p["best"] = t
            results.append((pilot, t, pts, medals.get(pos, f"#{pos+1}")))
        season = sorted(((pl, d["points"]) for pl, d in cst.items()),
                        key=lambda kv: -kv[1])

        # στατιστικά εβδομάδας για το site (Track Archive)
        records_broken = sum(1 for r in state.get("records_log", [])
                             if r.get("track") == track)
        standings["history"].append({
            "date": now, "track": track, "class": cls_key,
            "results": [{"pilot": pl, "time": t, "points": p} for pl, t, p, _ in results],
            "winner": results[0][0] if results else "",
            "best_time": results[0][1] if results else None,
            "pilots_count": len(results),
            "records_broken": records_broken,
        })
        out.append({"class": cls_key, "results": results, "season": season})

    if out:   # μόνο αν πραγματικά απονεμήθηκαν πόντοι
        awarded = standings.setdefault("awarded", [])
        if track not in awarded:
            awarded.append(track)
    save_standings(standings)
    return out
