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


def _quad_of(key: str) -> str:
    """Όνομα quad από το κλειδί εγγραφής 'πιλότος|μοντέλο'.

    - Αν το μοντέλο είναι κείμενο -> επιστρέφεται ως έχει.
    - Αν είναι αριθμητικό model_id -> μετάφραση μέσω quad_names.json.
    - Αλλιώς (κενό/None/άγνωστο id) -> "" (το site δεν εμφανίζει τίποτα).
    """
    parts = key.split("|", 1)
    if len(parts) > 1:
        quad = parts[1].strip()
        if quad and quad != "None":
            if not quad.isdigit():
                return quad
            import quad_names
            return quad_names.get_name(quad)
    return ""


def _auto_resolve_quads(track: str, weekly: dict) -> None:
    """Αυτόματη χαρτογράφηση άγνωστων model_id (ΜΙΑ ΚΑΙ ΕΞΩ).

    Για κάθε model_id που δεν είναι στο quad_names.json, ενώνει:
      - state.json (πιλότος + model_id) με
      - το website leaderboard (πιλότος + όνομα μοντέλου)
    και αποθηκεύει το mapping. Μελλοντικά exports βρίσκουν τα πάντα
    στην cache - κανένα ανθρώπινο βήμα δεν ξαναχρειάζεται.
    Τυχόν αποτυχία δικτύου -> σιωπηρή παράλειψη (ξαναδοκιμάζει την επόμενη φορά).
    """
    import db
    import quad_names

    track_id = weekly.get("track_id")
    if not track_id:
        return
    entries = db.load_state().get("tracks", {}).get(track, {})
    known = quad_names.load()
    unknown = set()
    for cls_entries in entries.values():
        for key in cls_entries:
            parts = key.split("|", 1)
            if len(parts) > 1:
                mid = parts[1].strip()
                if mid.isdigit() and mid not in known:
                    unknown.add(mid)
    if not unknown:
        return

    try:
        import velocidrone_web as vw
        url = f"https://www.velocidrone.com/leaderboard/{track_id}"
        web_entries = vw.fetch_track(track, url)
    except Exception as e:
        print(f"[quad] website lookup απέτυχε (θα ξαναδοκιμαστεί): {e}")
        return
    if not web_entries:
        return

    web_by_pilot = {}
    for e in web_entries:
        mdl = (e.get("model") or "").strip()
        if mdl:
            web_by_pilot.setdefault(e["pilot"], set()).add(mdl)

    api_by_pilot = {}
    for cls_entries in entries.values():
        for key in cls_entries:
            parts = key.split("|", 1)
            if len(parts) > 1 and parts[1].strip().isdigit():
                api_by_pilot.setdefault(parts[0], set()).add(parts[1].strip())

    mapping = quad_names.load()
    resolved = 0
    for pilot, ids in api_by_pilot.items():
        if len(ids) == 1:
            mid = next(iter(ids))
            if mid in unknown:
                names = web_by_pilot.get(pilot, set())
                if len(names) == 1:
                    mapping[mid] = next(iter(names))
                    resolved += 1
    if resolved:
        quad_names.save(mapping)
        print(f"[quad] αυτόματη χαρτογράφηση: {resolved} νέα quads -> quad_names.json")


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
        _auto_resolve_quads(track, weekly)
        for cls, entries in state.get("tracks", {}).get(track, {}).items():
            best = {}
            for key, t in entries.items():
                pilot = key.split("|")[0]
                if pilot not in best or t < best[pilot][0]:
                    best[pilot] = (t, _quad_of(key))
            current[cls or "other"] = [
                {"pilot": p, "time": t, "quad": q} for p, (t, q) in
                sorted(best.items(), key=lambda kv: kv[1][0])
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
