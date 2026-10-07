"""
export_site_data.py

Εξάγει όλα τα δεδομένα του πρωταθλήματος σε ΕΝΑ αρχείο site_data.json
για χρήση από website. Τρέξε μετά από κάθε σάρωση (ή κάθε 15 λεπτά via task):

  python3 export_site_data.py && git add site_data.json && git commit -m "data" && git push

Το site διαβάζει το αρχείο από:
  https://raw.githubusercontent.com/alefas9/velocidrone-bot/main/site_data.json

Προσοχή: το repo πρέπει να είναι PUBLIC (ή χρησιμοποίησε GitHub Pages).
"""

import json
import os
from datetime import datetime

import db
import points


def _enrich_hist(h: dict) -> dict:
    """Συμπλήρωση πεδίων για παλιότερα history entries (που τα λείπουν)."""
    h = dict(h)
    results = h.get("results", [])
    if results:
        h.setdefault("winner", results[0].get("pilot", ""))
        h.setdefault("best_time", results[0].get("time"))
        h.setdefault("pilots_count", len(results))
    h.setdefault("records_broken", 0)
    return h


def export(path: str = "site_data.json") -> dict:
    state = db.load_state()
    standings = points.load_standings()

    # τρέχουσα πίστα
    weekly = {}
    if os.path.exists("weekly_track.json"):
        with open("weekly_track.json", encoding="utf-8") as f:
            weekly = json.load(f)

    # leaderboard τρέχουσας πίστας ανά κλάση (καλύτερος χρόνος ανά πιλότο)
    current = {}
    track = weekly.get("track")
    if track:
        for cls, entries in state.get("tracks", {}).get(track, {}).items():
            best = {}
            for key, t in entries.items():
                pilot = key.split("|")[0]
                if pilot not in best or t < best[pilot]:
                    best[pilot] = t
            current[cls or "other"] = [
                {"pilot": p, "time": t} for p, t in
                sorted(best.items(), key=lambda kv: kv[1])
            ]

    # βαθμολογία σεζόν ανά κλάση
    season = {}
    for cls, pilots in standings.get("classes", {}).items():
        season[cls] = [
            {"pilot": p, "points": d["points"], "wins": d["wins"],
             "podiums": d["podiums"], "best": d["best"]}
            for p, d in sorted(pilots.items(), key=lambda kv: -kv[1]["points"])
        ]

    # ενεργά duels (μη-resolved) για εμφάνιση στο site
    active_duels = []
    if os.path.exists("duels.json"):
        try:
            with open("duels.json", encoding="utf-8") as f:
                active_duels = [d for d in json.load(f) if not d.get("resolved")]
        except (json.JSONDecodeError, OSError):
            pass

    data = {
        "generated_at": datetime.now().isoformat(),
        "season": datetime.now().year,
        "current_track": track,
        "current_leaderboard": current,
        "season_standings": season,
        "history": [_enrich_hist(h) for h in standings.get("history", [])[-20:]],
        "duels": active_duels,                            # ενεργά duels
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


if __name__ == "__main__":
    d = export()
    print(f"OK -> site_data.json ({os.path.getsize('site_data.json')} bytes)")
    print(f"  πίστα: {d['current_track']} | κλάσεις: {list(d['current_leaderboard'])} | "
          f"σεζόν: {list(d['season_standings'])}")
