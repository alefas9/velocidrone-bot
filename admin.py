"""
admin.py

Χειροκίνητα admin εργαλεία (δεν χρειάζονται bot commands):

  python admin.py duel "Nikos" "Maria" "Bando Track" --days 3     -> δημιουργία duel
  python admin.py recap 2026 9 "Σεπτέμβριος 2026"                 -> μηνιαίο recap
  python admin.py category "Bando Track" racing                   -> tag σε κατηγορία
"""

import argparse
import datetime

from duels import create_duel
from monthly_recap import build_monthly_recap
from discord_notify import send_discord_message
import db


def cmd_duel(args) -> None:
    duel = create_duel(args.pilot_a, args.pilot_b, args.track, days=args.days)
    print(f"Δημιουργήθηκε duel: {duel['pilot_a']} vs {duel['pilot_b']} "
          f"στο «{duel['track']}» (deadline: {duel['deadline']})")


def cmd_recap(args) -> None:
    state = db.load_state()
    prefix = f"{args.year:04d}-{args.month:02d}"
    records = [r for r in state["records_log"] if r["date"].startswith(prefix)]
    label = args.label or datetime.date(args.year, args.month, 1).strftime("%B %Y")
    text = build_monthly_recap(label, records)
    send_discord_message(text)
    print(text)


def cmd_week(args) -> None:
    """Ο admin ορίζει την πίστα της εβδομάδας."""
    import json
    from config import WEEKLY_TRACK_FILE
    data = {"track": args.track, "url": args.url,
            "set_at": datetime.datetime.now().isoformat()}
    with open(WEEKLY_TRACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Πίστα εβδομάδας: «{args.track}» -> {args.url}")
    print("Το bot θα παρακολουθεί αυτόματα αυτή την πίστα σε κάθε σάρωση.")
    if not args.no_announce:
        from discord_notify import send_discord_message
        send_discord_message(
            f"📢 **Πίστα εβδομάδας: «{args.track}»**\n"
            f"Πετάξτε και ανεβάστε τους χρόνους σας! (Auto Leaderboard Upload: ON)\n"
            f"Καλή επιτυχία! 🚁"
        )


def cmd_week_clear(args) -> None:
    import os
    from config import WEEKLY_TRACK_FILE
    if os.path.exists(WEEKLY_TRACK_FILE):
        os.remove(WEEKLY_TRACK_FILE)
    print("Η πίστα εβδομάδας καθαρίστηκε.")


def cmd_category(args) -> None:
    import track_categories as tc
    tc.TRACK_CATEGORIES[args.track] = args.category
    print(f"Προστέθηκε προσωρινά στο runtime: '{args.track}' -> '{args.category}'")
    print("Για μόνιμη αποθήκευση, πρόσθεσέ το στο TRACK_CATEGORIES του track_categories.py")


def main() -> None:
    p = argparse.ArgumentParser(description="Admin εργαλεία Velocidrone bot")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("duel", help="δημιουργία duel")
    d.add_argument("pilot_a"); d.add_argument("pilot_b"); d.add_argument("track")
    d.add_argument("--days", type=int, default=3)
    d.set_defaults(func=cmd_duel)

    r = sub.add_parser("recap", help="μηνιαίο recap")
    r.add_argument("year", type=int); r.add_argument("month", type=int)
    r.add_argument("label", nargs="?", default=None)
    r.set_defaults(func=cmd_recap)

    w = sub.add_parser("week", help="ορισμός πίστας εβδομάδας (admin)")
    w.add_argument("track", help='όνομα πίστας, π.χ. "Bando Track"')
    w.add_argument("url", help="URL του leaderboard, π.χ. https://www.velocidrone.com/leaderboard/...")
    w.add_argument("--no-announce", action="store_true", help="χωρίς ανακοίνωση στο Discord")
    w.set_defaults(func=cmd_week)

    wc = sub.add_parser("week-clear", help="καθαρισμός πίστας εβδομάδας")
    wc.set_defaults(func=cmd_week_clear)

    c = sub.add_parser("category", help="tag track σε κατηγορία")
    c.add_argument("track"); c.add_argument("category")
    c.set_defaults(func=cmd_category)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
