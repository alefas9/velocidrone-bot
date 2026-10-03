"""
integration_example.py

ΔΕΝ είναι αρχείο για να τρέξει αυτόνομα - είναι παράδειγμα του πώς ενώνονται
όλα τα νέα κομμάτια μέσα στη ΔΙΚΗ ΣΟΥ υπάρχουσα λογική (π.χ. στο update_leaderboard.py).

Αντικατέστησε τα σημεία με "# TODO" με τον πραγματικό σου κώδικα / δεδομένα.
"""

from discord_notify import send_discord_message, send_discord_embed
from leaderboard_format import (
    format_leaderboard,
    format_leaderboard_discord_embed_fields,
    proximity_teaser,
)
from duels import update_duel_times, check_expired_duels
from track_categories import get_category, themed_day_label


def on_new_record_detected(track_name: str, pilot_name: str, new_time: float, full_leaderboard: list):
    """
    Κάλεσέ το ΑΜΕΣΩΣ μόλις το ήδη υπάρχον polling σου εντοπίσει νέο ρεκόρ
    (αντί να περιμένεις το τέλος της ημέρας - αυτό λύνει το "real-time" feature).

    :param full_leaderboard: η πλήρης, ήδη ταξινομημένη λίστα του track,
        π.χ. [{"pilot": "Nikos", "time": 58.342}, ...]
    """

    # 1) Real-time ανακοίνωση ρεκόρ (feature #1)
    category = get_category(track_name)
    category_label = themed_day_label(category) if category != "uncategorized" else ""

    header = f"🚁 Νέο ρεκόρ στο «{track_name}»! {category_label}".strip()
    body = f"**{pilot_name}** πέτυχε {new_time:.3f}s"

    send_discord_embed(
        title=header,
        description=body,
        fields=format_leaderboard_discord_embed_fields(full_leaderboard, top_n=5),
    )
    # + αντίστοιχο bot.send_message(...) για Telegram, με format_leaderboard(full_leaderboard)

    # 2) Proximity teaser (feature #2) - στέλνεται μόνο αν υπάρχει κάτι "δραματικό"
    teaser = proximity_teaser(full_leaderboard)
    if teaser:
        send_discord_message(teaser)
        # + bot.send_message(...) για Telegram

    # 3) Ενημέρωση τυχόν ενεργών duels (feature #5, απλοποιημένο)
    update_duel_times(track_name=track_name, pilot_name=pilot_name, new_time=new_time)


def daily_cron_extra_steps():
    """
    Κάλεσέ το μέσα στο ήδη υπάρχον daily cron job (μαζί με το select_track.py flow).
    """
    # Ανακοίνωσε duels που έληξαν σήμερα
    for announcement in check_expired_duels():
        send_discord_message(announcement)
        # + bot.send_message(...) για Telegram


# --- ΣΗΜΕΙΩΣΗ ΓΙΑ ΤΟ #3 (screenshot-style leaderboard) ---
# Δεν χρειάζεται ξεχωριστή συνάρτηση - το format_leaderboard() /
# format_leaderboard_discord_embed_fields() ΕΙΝΑΙ το emoji-styled leaderboard.
# Χρησιμοποιείται ήδη μέσα στο on_new_record_detected() παραπάνω.

# --- ΣΗΜΕΙΩΣΗ ΓΙΑ ΤΟ #6 (μηνιαίο recap) ---
# Δες monthly_recap.py - τρέχεται ξεχωριστά, 1η του μήνα, όχι σε κάθε ρεκόρ.
