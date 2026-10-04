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
    """Ο admin ανακοινώνει την πίστα της εβδομάδας (csv mode - community tracks).

    Χωρίς URL: απλή ανακοίνωση στο Discord. Ο διοργανωτής κάνει export το CSV
    από το in-game leaderboard και το ρίχνει στον φάκελο tracks/ (ή root).
    Με URL: ενεργοποιείται και το web mode (μόνο για verified πίστες).
    """
    if args.track_id:
        import json
        from config import WEEKLY_TRACK_FILE
        data = {"track": args.track, "track_id": int(args.track_id),
                "race_mode": int(args.race_mode),
                "set_at": datetime.datetime.now().isoformat()}
        with open(WEEKLY_TRACK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Πίστα εβδομάδας (API mode): «{args.track}» id={args.track_id} race_mode={args.race_mode}")
        print("Το bot θα τραβάει αυτόματα τους χρόνους κάθε 5 λεπτά - κανένα CSV!")
    elif args.url:
        import json
        from config import WEEKLY_TRACK_FILE
        data = {"track": args.track, "url": args.url,
                "set_at": datetime.datetime.now().isoformat()}
        with open(WEEKLY_TRACK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Πίστα εβδομάδας (web mode): «{args.track}» -> {args.url}")
    else:
        print(f"Πίστα εβδομάδας (csv mode): «{args.track}»")
        print("Ο διοργανωτής κάνει export το CSV in-game και το ανεβάζει στον φάκελο του NAS.")
    if not args.no_announce:
        from discord_notify import send_discord_message
        from messages import WEEK_ANNOUNCE, pick
        send_discord_message(pick(WEEK_ANNOUNCE).format(track=args.track) + "\n"
                             "(Auto Leaderboard Upload: ON)")


def cmd_week_clear(args) -> None:
    import os
    from config import WEEKLY_TRACK_FILE
    if os.path.exists(WEEKLY_TRACK_FILE):
        os.remove(WEEKLY_TRACK_FILE)
    print("Η πίστα εβδομάδας καθαρίστηκε.")


def cmd_whitelist(args) -> None:
    import whitelist as wlm
    if args.action == "add":
        added = wlm.add(args.names)
        print(f"Προστέθηκαν {added} μέλη. Σύνολο: {len(wlm.load())}")
    elif args.action == "remove":
        removed = wlm.remove(args.names)
        print(f"Αφαιρέθηκαν {removed}. Σύνολο: {len(wlm.load())}")
    else:
        rows = wlm.members()
        if rows:
            print(f"Whitelist ({len(rows)} μέλη) - αρχείο: whitelist.csv")
            print(f"  {'ΟΝΟΜΑ':<18} {'DISCORD':<18} {'ΚΛΑΣΗ'}")
            for r in rows:
                print(f"  {r['name']:<18} {r.get('discord',''):<18} {r.get('class','')}")
        else:
            print("Whitelist άδεια -> όλοι οι πιλότοι ορατοί.")


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
    w.add_argument("url", nargs="?", default=None,
                   help="προαιρετικό URL (μόνο verified πίστες) - χωρίς αυτό λειτουργεί με CSV export")
    w.add_argument("--track-id", type=int, default=None,
                   help="Velocidrone track id (API mode - αυτόματο, για ΟΛΕΣ τις πίστες)")
    w.add_argument("--race-mode", type=int, default=6,
                   help="race mode (default 6 = single class 3 laps)")
    w.add_argument("--no-announce", action="store_true", help="χωρίς ανακοίνωση στο Discord")
    w.set_defaults(func=cmd_week)

    wc = sub.add_parser("week-clear", help="καθαρισμός πίστας εβδομάδας")
    wc.set_defaults(func=cmd_week_clear)

    wl = sub.add_parser("whitelist", help="διαχείριση μελών κοινότητας")
    wl.add_argument("action", choices=["add", "remove", "list"])
    wl.add_argument("names", nargs="*", help="ονόματα πιλότων (όπως στο Velocidrone)")
    wl.set_defaults(func=cmd_whitelist)

    c = sub.add_parser("category", help="tag track σε κατηγορία")
    c.add_argument("track"); c.add_argument("category")
    c.set_defaults(func=cmd_category)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
