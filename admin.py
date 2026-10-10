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


DUEL_START = [
    "🥊 ΞΕΚΙΝΗΣΕ ΤΟ ΜΠΑΡΑΖ: {a} vs {b} στην «{track}»! Προθεσμία: {days} μέρες - καλή τύχη και οι δύο! 🏁",
    "⚔️ DUEL TIME! {a} εναντίον {b} στην «{track}»! Έχετε {days} μέρες - ο καλύτερος χρόνος κερδίζει! 🥊",
    "🔥 Νέο duel στον αέρα: {a} vs {b} στην «{track}»! {days} μέρες προθεσμία - πιάστε τα γκάζια! ⛽",
]


def cmd_duel(args) -> None:
    duel = create_duel(args.pilot_a, args.pilot_b, args.track, days=args.days)
    print(f"Δημιουργήθηκε duel: {duel['pilot_a']} vs {duel['pilot_b']} "
          f"στο «{duel['track']}» (deadline: {duel['deadline']})")
    if not getattr(args, "no_announce", False):
        import random
        from discord_notify import send_discord_message
        from whitelist import mention_map, to_mention
        mm = mention_map()
        ids = [mm[k] for k in (args.pilot_a.lower(), args.pilot_b.lower()) if k in mm]
        body = random.choice(DUEL_START).format(
            a=to_mention(args.pilot_a, mm), b=to_mention(args.pilot_b, mm),
            track=args.track, days=args.days)
        send_discord_message(body, mentions=ids)


def cmd_recap(args) -> None:
    state = db.load_state()
    prefix = f"{args.year:04d}-{args.month:02d}"
    records = [r for r in state["records_log"] if r["date"].startswith(prefix)]
    label = args.label or datetime.date(args.year, args.month, 1).strftime("%B %Y")
    text = build_monthly_recap(label, records)
    send_discord_message(text)
    print(text)


def _maybe_award_previous(args) -> None:
    """Αν υπήρχε προηγούμενη πίστα, απονομή πόντων πριν την αντικατάσταση."""
    import json, os
    from config import WEEKLY_TRACK_FILE
    if getattr(args, "no_award", False):
        return
    if not os.path.exists(WEEKLY_TRACK_FILE):
        return
    with open(WEEKLY_TRACK_FILE, encoding="utf-8") as f:
        prev = json.load(f)
    prev_track = prev.get("track")
    if not prev_track or prev_track == getattr(args, "track", None):
        return  # δεν υπήρχε προηγούμενη ή ίδια πίστα
    import db
    import points
    state = db.load_state()
    if prev_track not in state.get("tracks", {}):
        print(f"(δεν βρέθηκαν δεδομένα για την προηγούμενη πίστα «{prev_track}» - παράλειψη απονομής)")
        return
    results = points.award_week(prev_track, state,
                                force=getattr(args, "force_award", False))
    if not results:
        return
    from discord_notify import send_discord_embed
    from messages import pick
    for r in results:
        lines = [f"{m} **{pl}**  {t:.3f}s  (+{p})" for pl, t, p, m in r["results"]]
        send_discord_embed(
            title=f"🏆 Εβδομάδα ολοκληρώθηκε: «{prev_track}» [{r['class']}]",
            description="\n".join(lines) if lines else "(κενή κατάταξη)",
        )
        season_lines = [f"**{i+1}.** {pl} — {p} βαθμοί" for i, (pl, p) in enumerate(r["season"][:10])]
        send_discord_embed(
            title=f"📊 Βαθμολογία σεζόν [{r['class']}]",
            description="\n".join(season_lines),
            color=0x3498DB,
        )
    print(f"Απονεμήθηκαν πόντοι για «{prev_track}» ({len(results)} κλάσεις)")


def cmd_duel_list(args) -> None:
    import duels as dm
    duels = [d for d in dm._load_duels() if not d.get("resolved")]
    if not duels:
        print("Κανένα ενεργό duel.")
        return
    print(f"Ενεργά duels ({len(duels)}):")
    for d in duels:
        print(f"  🥊 {d['pilot_a']} vs {d['pilot_b']} | «{d['track']}» | λήγει: {d['deadline'][:10]}")


def cmd_duel_cancel(args) -> None:
    import duels as dm
    duels = dm._load_duels()
    before = len(duels)
    duels = [d for d in duels if not (
        d["pilot_a"].lower() == args.pilot_a.strip().lower()
        and d["pilot_b"].lower() == args.pilot_b.strip().lower())]
    dm._save_duels(duels)
    removed = before - len(duels)
    print(f"Ακυρώθηκαν {removed} duel(s): {args.pilot_a} vs {args.pilot_b}")
    if removed and not args.no_announce:
        from discord_notify import send_discord_message
        send_discord_message(f"❌ Ακυρώθηκε το duel: {args.pilot_a} vs {args.pilot_b}")


def cmd_test_gif(args) -> None:
    """Ολοκληρωμένο self-test GIF - τα αποτελέσματα πάνε στο ADMIN κανάλι."""
    import time
    import gif_fetcher
    from discord_notify import send_discord_admin_message, send_discord_embed

    info = None
    for attempt in range(3):
        info = gif_fetcher.fetch_gif_full("new_top")
        if info:
            break
        time.sleep(2)

    if not info:
        send_discord_admin_message(
            "🧪 **GIF TEST ΑΠΟΤΥΧΙΑ**\nΤο fetch επέστρεψε κενό. Έλεγξε GIPHY_API_KEY / δίκτυο.")
        print("ΑΠΟΤΥΧΙΑ: κενό fetch")
        return

    # κατέβασμα GIF για συνημμένο
    gif_bytes = None
    try:
        import requests as _rq
        rr = _rq.get(info["media"], timeout=15)
        if rr.ok and 1000 < len(rr.content) < 8_000_000:
            gif_bytes = rr.content
    except Exception:
        pass

    mode = f"ATTACH ({len(gif_bytes)//1024}KB)" if gif_bytes else "LINK"
    send_discord_admin_message(
        f"🧪 **GIF TEST** ({mode})\npage: `{info['page'][:70]}`\nΣτέλνω δοκιμαστικό (μόνο εδώ)...")
    from discord_notify import send_discord_admin_embed
    send_discord_admin_embed(
        title="🧪 ΔΟΚΙΜΗ GIF",
        description="Αν βλέπεις GIF να παίζει, όλα δουλεύουν! 🎬",
        image=info["page"] if not gif_bytes else None,
        attachment=gif_bytes)
    print("OK - αποτελέσματα στο admin κανάλι")


def cmd_standings(args) -> None:
    import points
    from discord_notify import send_discord_embed
    data = points.load_standings()
    classes = data.get("classes", {})
    if not classes:
        print("Κενή βαθμολογία - δεν έχει ολοκληρωθεί καμία εβδομάδα ακόμα.")
        return
    for cls, pilots in classes.items():
        season = sorted(pilots.items(), key=lambda kv: -kv[1]["points"])
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        lines = [f"{medals.get(i, f'**{i+1}.**')} {pl} — **{d['points']}** βαθμοί "
                 f"({d['wins']} νίκες, {d['podiums']} podiums)"
                 for i, (pl, d) in enumerate(season[:15])]
        send_discord_embed(title=f"📊 Βαθμολογία σεζόν [{cls}]", description="\n".join(lines), color=0x3498DB)
        print(f"Βαθμολογία [{cls}]: {len(season)} πιλότοι -> Discord")


def cmd_award(args) -> None:
    """Χειροκίνητη απονομή για την ΤΡΕΧΟΥΣΑ πίστα (χωρίς αλλαγή)."""
    import json, os, db, points
    from config import WEEKLY_TRACK_FILE
    if not os.path.exists(WEEKLY_TRACK_FILE):
        print("Δεν έχει οριστεί πίστα εβδομάδας.")
        return
    with open(WEEKLY_TRACK_FILE, encoding="utf-8") as f:
        weekly = json.load(f)
    track = weekly.get("track")
    state = db.load_state()
    res = points.award_week(track, state, force=getattr(args, "force_award", False))
    if res:
        print(f"Απονεμήθηκαν πόντοι για «{track}»: {sum(len(r['results']) for r in res)} εγγραφές")
    else:
        print("Δεν απονεμήθηκαν πόντοι (ήδη απονεμημένο ή κενή κατάταξη).")


def cmd_standings_reset(args) -> None:
    import os
    from config import STATE_FILE  # noqa
    f = points_standings_file()
    if os.path.exists(f):
        os.remove(f)
    print("Βαθμολογία σεζόν μηδενίστηκε. Νέα σεζόν, καθαρό πεδίο! 🏁")


def points_standings_file() -> str:
    import os
    return os.environ.get("STANDINGS_FILE", "standings.json")


def cmd_model(args) -> None:
    import velocidrone_api as va
    if str(args.model_id).lower() == "list" or args.cls is None and not str(args.model_id).isdigit():
        mapping = va.load_model_classes()
        inv = {}
        for mid, cls in sorted(mapping.items()):
            inv.setdefault(cls, []).append(mid)
        for cls, ids in inv.items():
            print(f"  {cls}: {ids}")
        unknown = args.model_id if hasattr(args, "model_id") else None
        print("\n(τα ids που ΔΕΝ είναι εδώ βγαίνουν 'other' - πρόσθεσέ τα με: model <id> <class>)")
    else:
        va.set_model_class(int(args.model_id), args.cls)
        print(f"✓ model_id {args.model_id} -> {args.cls} (model_classes.json)")


def cmd_quad(args) -> None:
    """Χάρτης model_id -> όνομα quad (persisted, για site/Discord).

    Χρήση:
      python3 admin.py quad                 # προβολή χάρτη
      python3 admin.py quad scan            # όλα τα ids στο state + πιλότοι
      python3 admin.py quad 123 "Five33 Switchback"   # ορισμός ενός
    """
    import quad_names
    if args.model_id == "scan":
        import db
        state = db.load_state()
        ids = {}
        for track, classes in state.get("tracks", {}).items():
            for cls, entries in classes.items():
                for key in entries:
                    parts = key.split("|", 1)
                    if len(parts) > 1 and parts[1].strip().isdigit():
                        ids.setdefault(parts[1].strip(), set()).add(parts[0])
        mapping = quad_names.load()
        print("model_ids στο leaderboard και ποιοι τα πετούν:")
        if not ids:
            print("  (κανένα - το state είναι κενό)")
        for mid in sorted(ids, key=int):
            name = mapping.get(mid, "")
            tag = name if name else "(ΧΩΡΙΣ ΟΝΟΜΑ)"
            print(f"  {mid}: {tag}   <- {', '.join(sorted(ids[mid]))}")
        missing = [m for m in ids if m not in mapping]
        if missing:
            print(f"\nΧωρίς όνομα: {', '.join(missing)}")
            print('Ορίστε τα: python3 admin.py quad <id> "<όνομα>"')
        return
    if args.model_id is not None and args.name:
        quad_names.set_name(args.model_id, args.name)
        print(f"✓ model_id {args.model_id} -> «{args.name}» (quad_names.json)")
    mapping = quad_names.load()
    print("\nΧάρτης model_id -> όνομα quad:")
    if not mapping:
        print('  (κενός - ορίστε με: python3 admin.py quad <id> "<όνομα>")')
    else:
        for mid in sorted(mapping, key=lambda x: int(x)):
            print(f"  {mid}: {mapping[mid]}")


def cmd_week(args) -> None:
    """Ο admin ανακοινώνει την πίστα της εβδομάδας (csv mode - community tracks).

    Χωρίς URL: απλή ανακοίνωση στο Discord. Ο διοργανωτής κάνει export το CSV
    από το in-game leaderboard και το ρίχνει στον φάκελο tracks/ (ή root).
    Με URL: ενεργοποιείται και το web mode (μόνο για verified πίστες).
    """
    if args.track_id:
        import json
        from config import WEEKLY_TRACK_FILE
        # Αυτόματο κλείσιμο προηγούμενης εβδομάδας: απονομή πόντων
        _maybe_award_previous(args)
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
    d.add_argument("--no-announce", action="store_true", help="χωρίς ανακοίνωση στο Discord")
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
    w.add_argument("--no-award", action="store_true",
                   help="χωρίς απονομή πόντων προηγούμενης εβδομάδας")
    w.add_argument("--force-award", action="store_true",
                   help="απονομή ακόμα κι αν η προηγούμενη πίστα έχει ήδη βαθμολογηθεί")
    w.add_argument("--no-announce", action="store_true", help="χωρίς ανακοίνωση στο Discord")
    w.set_defaults(func=cmd_week)

    wc = sub.add_parser("week-clear", help="καθαρισμός πίστας εβδομάδας")
    wc.set_defaults(func=cmd_week_clear)

    m = sub.add_parser("model", help="χάρτης model_id -> κλάση (5inch/whoop/...)")
    m.add_argument("model_id", help="το model_id από το API (π.χ. 123) ή 'list'")
    m.add_argument("cls", nargs="?", default=None, help="κλάση (5inch/whoop) - μόνο για ορισμό")
    m.set_defaults(func=cmd_model)

    qn = sub.add_parser("quad", help="χάρτης model_id -> όνομα quad (για site/Discord)")
    qn.add_argument("model_id", nargs="?", default=None,
                    help="το model_id (π.χ. 123) - κενό για προβολή χάρτη")
    qn.add_argument("name", nargs="?", default=None,
                    help="όνομα quad σε εισαγωγικά (π.χ. \"Five33 Switchback\")")
    qn.set_defaults(func=cmd_quad)

    tg = sub.add_parser("test-gif", help="self-test GIF -> αποτελέσματα στο admin κανάλι")
    tg.set_defaults(func=cmd_test_gif)

    dl = sub.add_parser("duel-list", help="προβολή ενεργών duels")
    dl.set_defaults(func=cmd_duel_list)

    dc = sub.add_parser("duel-cancel", help="ακύρωση duel (διαγράφει ΟΛΑ τα duels του ζευγαριού)")
    dc.add_argument("pilot_a")
    dc.add_argument("pilot_b")
    dc.add_argument("--no-announce", action="store_true")
    dc.set_defaults(func=cmd_duel_cancel)

    st = sub.add_parser("standings", help="βαθμολογία σεζόν -> Discord")
    st.set_defaults(func=cmd_standings)

    aw = sub.add_parser("award", help="απονομή πόντων τρέχουσας πίστας τώρα")
    aw.add_argument("--force-award", action="store_true",
                    help="απονομή ακόμα κι αν έχει ήδη γίνει (διπλοί πόντοι!)")
    aw.set_defaults(func=cmd_award)

    sr = sub.add_parser("standings-reset", help="μηδενισμός βαθμολογίας (νέα σεζόν)")
    sr.set_defaults(func=cmd_standings_reset)

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
