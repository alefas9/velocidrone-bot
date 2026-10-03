"""
track_categories.py

ΑΠΛΟΠΟΙΗΜΕΝΗ υλοποίηση θεματικών προκλήσεων.

Αντί για πολύπλοκο auto-detect, χρησιμοποιούμε ένα απλό dictionary
όπου ΕΣΥ (χειροκίνητα, μία φορά) κατηγοριοποιείς τα tracks που ήδη
χρησιμοποιεί το bot. Μετά η επιλογή track μπορεί να φιλτράρει με βάση
κατηγορία όποτε θες "themed" ημέρα/εβδομάδα.

Δεν χρειάζεται database migration - είναι απλά ένα .py αρχείο που
το ενημερώνεις όποτε προσθέτεις νέο track.
"""

# Πρόσθεσε εδώ τα δικά σου track names -> κατηγορία.
# Οι κατηγορίες είναι ελεύθερες, βάλε ό,τι ταιριάζει στο community σου.
TRACK_CATEGORIES = {
    # "Track Name Ακριβώς Όπως Στο Velocidrone": "category",
    "Example Freestyle Arena": "freestyle",
    "Example Whoop Gym": "whoop",
    "Example Race Track A": "racing",
}

CATEGORY_LABELS = {
    "freestyle": "🎪 Freestyle Quads",
    "whoop": "🐝 Whoop Only",
    "racing": "🏁 Racing",
}


def get_category(track_name: str) -> str:
    """Επιστρέφει την κατηγορία ενός track, ή 'uncategorized' αν δεν έχει μπει ακόμα."""
    return TRACK_CATEGORIES.get(track_name, "uncategorized")


def tracks_by_category(category: str) -> list:
    """Λίστα με όλα τα tracks μιας κατηγορίας - χρήσιμο για 'themed day' επιλογή."""
    return [name for name, cat in TRACK_CATEGORIES.items() if cat == category]


def themed_day_label(category: str) -> str:
    """Το label που εμφανίζεται στο ανακοινωτικό μήνυμα της ημέρας."""
    return CATEGORY_LABELS.get(category, category)


# --- Παράδειγμα ενσωμάτωσης στο select_track.py ---
#
# import random
# from track_categories import tracks_by_category, themed_day_label
#
# # Κάθε Παρασκευή -> whoop-only ημέρα (παράδειγμα)
# import datetime
# if datetime.date.today().weekday() == 4:  # 4 = Friday
#     candidates = tracks_by_category("whoop")
#     if candidates:
#         chosen_track = random.choice(candidates)
#         announcement = f"{themed_day_label('whoop')}\nΣημερινό track: {chosen_track}"
#     else:
#         # fallback στην κανονική τυχαία επιλογή αν δεν υπάρχουν tagged tracks
#         chosen_track = random.choice(all_tracks)
# else:
#     chosen_track = random.choice(all_tracks)
