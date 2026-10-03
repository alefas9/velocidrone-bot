"""
duels.py

ΑΠΛΟΠΟΙΗΜΕΝΗ υλοποίηση head-to-head duels.

Αντί για πλήρες σύστημα προκλήσεων με commands μέσα στο Telegram/Discord
(που θα χρειαζόταν bot που "ακούει" απαντήσεις, states, timeouts κλπ),
κάνουμε το εξής απλό:

- Αποθηκεύουμε τα duels σε ένα .json αρχείο (όχι πλήρη database - αρκεί για
  μικρό community).
- Εσύ (ή όποιος έχει access) δημιουργεί ένα duel χειροκίνητα (2 πιλότες + track)
  μέσω μιας απλής συνάρτησης / μικρού command line script.
- Το bot απλά ελέγχει, όποτε κάνει το κανονικό του leaderboard polling, αν κάποιο
  από τα δύο ονόματα του ενεργού duel βελτίωσε χρόνο στο συγκεκριμένο track, και
  ανακοινώνει το αποτέλεσμα αυτόματα όταν λήξει η προθεσμία.

Αυτό γλιτώνει όλο το "custom bot commands" κομμάτι, που είναι το πιο περίπλοκο
μέρος ενός πλήρους duel συστήματος.
"""

import json
import os
from datetime import datetime, timedelta

DUELS_FILE = os.environ.get("DUELS_FILE", "duels.json")


def _load_duels() -> list:
    if not os.path.exists(DUELS_FILE):
        return []
    with open(DUELS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_duels(duels: list) -> None:
    with open(DUELS_FILE, "w", encoding="utf-8") as f:
        json.dump(duels, f, ensure_ascii=False, indent=2)


def create_duel(pilot_a: str, pilot_b: str, track_name: str, days: int = 3) -> dict:
    """
    Δημιουργεί ένα νέο duel. Κάλεσέ το χειροκίνητα (π.χ. από ένα μικρό script ή
    admin command) όποτε δύο πιλότες συμφωνήσουν σε πρόκληση.
    """
    duel = {
        "pilot_a": pilot_a,
        "pilot_b": pilot_b,
        "track": track_name,
        "created_at": datetime.utcnow().isoformat(),
        "deadline": (datetime.utcnow() + timedelta(days=days)).isoformat(),
        "best_time_a": None,
        "best_time_b": None,
        "resolved": False,
    }
    duels = _load_duels()
    duels.append(duel)
    _save_duels(duels)
    return duel


def update_duel_times(track_name: str, pilot_name: str, new_time: float) -> None:
    """
    Κάλεσέ το από το ήδη υπάρχον leaderboard polling κώδικα, κάθε φορά που
    ανιχνεύεται νέος χρόνος για κάποιον πιλότη σε κάποιο track. Αν ο πιλότης/track
    ταιριάζει με ενεργό duel, ενημερώνει το προσωπικό ρεκόρ μέσα στο duel.
    """
    duels = _load_duels()
    changed = False
    for duel in duels:
        if duel["resolved"] or duel["track"] != track_name:
            continue
        if pilot_name == duel["pilot_a"]:
            if duel["best_time_a"] is None or new_time < duel["best_time_a"]:
                duel["best_time_a"] = new_time
                changed = True
        elif pilot_name == duel["pilot_b"]:
            if duel["best_time_b"] is None or new_time < duel["best_time_b"]:
                duel["best_time_b"] = new_time
                changed = True
    if changed:
        _save_duels(duels)


def check_expired_duels() -> list:
    """
    Κάλεσέ το περιοδικά (π.χ. μία φορά τη μέρα, μαζί με το υπόλοιπο cron).
    Επιστρέφει λίστα με μηνύματα-ανακοινώσεις για duels που έληξαν, και τα
    μαρκάρει ως resolved ώστε να μην ξαναανακοινωθούν.
    """
    duels = _load_duels()
    announcements = []
    now = datetime.utcnow()
    changed = False

    for duel in duels:
        if duel["resolved"]:
            continue
        if datetime.fromisoformat(duel["deadline"]) > now:
            continue  # δεν έληξε ακόμα

        a, b = duel["pilot_a"], duel["pilot_b"]
        ta, tb = duel["best_time_a"], duel["best_time_b"]

        if ta is None and tb is None:
            msg = f"🤷 Το duel {a} vs {b} στο «{duel['track']}» έληξε χωρίς κανέναν χρόνο. Άκυρο!"
        elif ta is None:
            msg = f"🏆 Ο/Η {b} κερδίζει το duel εναντίον του/της {a} στο «{duel['track']}» (ο/η {a} δεν έβαλε χρόνο)!"
        elif tb is None:
            msg = f"🏆 Ο/Η {a} κερδίζει το duel εναντίον του/της {b} στο «{duel['track']}» (ο/η {b} δεν έβαλε χρόνο)!"
        elif ta < tb:
            msg = f"🏆 Ο/Η {a} κερδίζει το duel εναντίον του/της {b} στο «{duel['track']}»! {ta:.3f}s vs {tb:.3f}s"
        else:
            msg = f"🏆 Ο/Η {b} κερδίζει το duel εναντίον του/της {a} στο «{duel['track']}»! {tb:.3f}s vs {ta:.3f}s"

        announcements.append(msg)
        duel["resolved"] = True
        changed = True

    if changed:
        _save_duels(duels)

    return announcements


# --- Παράδειγμα ενσωμάτωσης ---
#
# 1) Όταν δύο πιλότες συμφωνούν σε πρόκληση (χειροκίνητα, π.χ. σε ένα REPL):
#    from duels import create_duel
#    create_duel("Nikos", "Maria", "Example Race Track A", days=3)
#
# 2) Μέσα στο ήδη υπάρχον update_leaderboard.py, κάθε φορά που βρίσκεις νέο χρόνο:
#    from duels import update_duel_times
#    update_duel_times(track_name=track, pilot_name=pilot, new_time=time_seconds)
#
# 3) Μία φορά τη μέρα (π.χ. στο ίδιο cron job με το select_track.py):
#    from duels import check_expired_duels
#    from discord_notify import send_discord_message
#    for announcement in check_expired_duels():
#        send_discord_message(announcement)
#        # + bot.send_message(...) για Telegram
