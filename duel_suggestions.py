"""
duel_suggestions.py

Αυτόματες προτάσεις duels: το bot παρακολουθεί τα κλειστά «ντέρμπι» ανάμεσα
σε μέλη της κοινότητας. Αν δύο πιλότοι μείνουν κοντά (λιγότερο από GAP_THRESHOLD
δευτερόλεπτα διαφορά) για τουλάχιστον MIN_DAYS μέρες, προτείνει duel στο Discord.
Κάθε ζευγάρι προτείνεται ΜΙΑ φορά (θυμάται στο duel_suggestions.json).

Ο admin στη συνέχεια μπορεί να «παντρέψει» χειροκίνητα:
  python3 admin.py duel "ZOUP" "tomahok" "SimRush Week1" --days 3
"""

import json
import os
from datetime import datetime, timedelta

SUGGESTIONS_FILE = os.environ.get("DUEL_SUGGESTIONS_FILE", "duel_suggestions.json")

GAP_THRESHOLD = 2.0    # διαφορά σε δευτερόλεπτα για να θεωρηθεί «ντέρμπι»
MIN_DAYS = 1           # πόσες μέρες πρέπει να μείνουν κοντά πριν προταθεί duel
CHECK_TOP = 10          # έλεγχε ζευγάρια μόνο μέσα στις πρώτες θέσεις κάθε κλάσης


def _load() -> dict:
    if not os.path.exists(SUGGESTIONS_FILE):
        return {}
    try:
        with open(SUGGESTIONS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    with open(SUGGESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_suggestions(track: str, groups: dict, now=None) -> list:
    """Ενημέρωσε την παρακολούθηση και επίστρεψε νέες προτάσεις (λίστα strings)."""
    now = now or datetime.utcnow()
    data = _load()
    current_pairs = set()
    suggestions = []

    for cls, group in groups.items():
        for i in range(min(CHECK_TOP, len(group) - 1)):
            leader, chaser = group[i], group[i + 1]
            gap = chaser["time"] - leader["time"]
            if gap > GAP_THRESHOLD:
                continue
            key = f"{track}|{leader['pilot']}|{chaser['pilot']}"
            current_pairs.add(key)
            entry = data.get(key)
            if entry and entry.get("suggested"):
                continue  # ήδη προτάθηκε παλιότερα
            if entry is None:
                entry = {"first_seen": now.isoformat(), "suggested": False}
                data[key] = entry
            first_seen = datetime.fromisoformat(entry["first_seen"])
            if now - first_seen >= timedelta(days=MIN_DAYS) and not entry["suggested"]:
                entry["suggested"] = True
                days = (now - first_seen).days
                suggestions.append({
                    "leader": leader["pilot"], "chaser": chaser["pilot"],
                    "gap": gap, "days": days, "track": track, "class": cls,
                })

    # καθάρισε ζευγάρια που δεν είναι πια κοντά (για να μη φουσκώνει το αρχείο)
    # κράτα τα suggested (ιστορικό) για 30 μέρες
    cutoff = now - timedelta(days=30)
    for key in list(data.keys()):
        if key not in current_pairs:
            if data[key].get("suggested"):
                first = datetime.fromisoformat(data[key]["first_seen"])
                if first < cutoff:
                    del data[key]
            else:
                del data[key]   # χάλασε το ντέρμπι -> ξεχνάμε, μπορεί να ξαναρχίσει

    _save(data)
    return suggestions
