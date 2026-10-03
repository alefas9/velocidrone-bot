"""
monthly_recap.py

ΑΠΛΟΠΟΙΗΜΕΝΗ εκδοχή του "μηνιαίου recap βίντεο" -> κείμενο + emojis αντί για video.
Καλύπτει την ίδια ανάγκη (μηνιαία ανασκόπηση, αίσθηση γιορτής/ορόσημου) χωρίς να
χρειάζεται pipeline παραγωγής βίντεο.

Χρησιμοποιεί δεδομένα που το bot ήδη συλλέγει (results ανά μέρα) - πρέπει απλά
να τα περάσεις μέσα σε αυτή τη μορφή (λίστα από dicts).
"""

from collections import Counter


def build_monthly_recap(month_label: str, daily_records: list) -> str:
    """
    :param month_label: π.χ. "Ιούλιος 2026"
    :param daily_records: λίστα από dicts, ένα per νέο ρεκόρ που καταγράφηκε μέσα
        στο μήνα, π.χ.
        [
            {"pilot": "Nikos", "track": "Example Race Track A", "time": 58.342, "date": "2026-07-03"},
            {"pilot": "Maria", "track": "Example Whoop Gym", "time": 40.1, "date": "2026-07-05"},
            ...
        ]
    :return: έτοιμο κείμενο για post
    """
    if not daily_records:
        return f"📅 Μηνιαίο Recap — {month_label}\n\nΔεν καταγράφηκαν νέα ρεκόρ αυτόν τον μήνα."

    total_records = len(daily_records)
    pilot_counts = Counter(r["pilot"] for r in daily_records)
    top_pilot, top_pilot_count = pilot_counts.most_common(1)[0]
    unique_tracks = len({r["track"] for r in daily_records})

    lines = [
        f"📅 **Μηνιαίο Recap — {month_label}**",
        "",
        f"🎯 Σύνολο νέων ρεκόρ: {total_records}",
        f"🗺️ Διαφορετικά tracks με ρεκόρ: {unique_tracks}",
        f"👑 Πιο ενεργός πιλότης: {top_pilot} ({top_pilot_count} ρεκόρ)",
        "",
        "🏆 Highlights:",
    ]

    # Δείξε τα 5 πιο πρόσφατα ρεκόρ σαν "highlights"
    for r in daily_records[-5:]:
        lines.append(f"  • {r['pilot']} — {r['track']} — {r['time']:.3f}s ({r['date']})")

    return "\n".join(lines)


# --- Παράδειγμα ενσωμάτωσης ---
#
# Τρέξε το 1η του μήνα (cron), αφού πρώτα μαζέψεις τα daily_records από τη db.py σου:
#
# from monthly_recap import build_monthly_recap
# from discord_notify import send_discord_message
#
# records = db.get_records_for_month(2026, 7)  # πρέπει να το φτιάξεις στο db.py σου
# recap_text = build_monthly_recap("Ιούλιος 2026", records)
# send_discord_message(recap_text)
# # + bot.send_message(...) για Telegram
