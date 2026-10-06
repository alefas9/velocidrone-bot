"""
update_leaderboard.py

ΤΟ ΚΥΡΙΟ SCRIPT - το δέσιμο όλων των κομματιών.

Τρόποι χρήσης:
  python update_leaderboard.py --once          # μία σάρωση τώρα (για cron/manual)
  python update_leaderboard.py --loop 300      # συνεχές polling κάθε 300s
  python update_leaderboard.py --once --demo   # δοκιμή με τα demo CSV (χωρίς Velocidrone)

Flow:
  1. Διαβάζει τα CSV leaderboards από το TRACKS_DIR
  2. Συγκρίνει με το state.json -> βρίσκει νέες βελτιώσεις χρόνων
  3. Για κάθε βελτίωση: Discord ανακοίνωση (embed) - teaser/duel ανά track
  4. Καλεί τα daily extras (duels που έληξαν)
  Πρώτη φορά που βλέπει ένα track: σιωπηλό import (χωρίς spam).

Πηγές δεδομένων (--source):
  web  : αυτόματο polling του velocidrone.com (TRACK_URLS/SCENERY_IDS στο .env)
  csv  : χειροκίνητα CSV exports στον φάκελο tracks/
  auto : web αν έχει οριστεί TRACK_URLS/SCENERY_IDS, αλλιώς csv (default)
"""

import argparse
import datetime
import time

from config import TRACKS_DIR, TOP_N
import db
from discord_notify import send_discord_message, send_discord_embed
from leaderboard_format import format_leaderboard_discord_embed_fields, proximity_teaser
from duels import update_duel_times, check_expired_duels
from track_categories import get_category, themed_day_label
from velocidrone_source import load_all_tracks
from config import TRACK_URLS, SCENERY_IDS


def _get_weekly():
    import json, os
    from config import WEEKLY_TRACK_FILE
    if os.path.exists(WEEKLY_TRACK_FILE):
        with open(WEEKLY_TRACK_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None


def load_tracks(tracks_dir: str, source: str) -> dict:
    """Επιλογή πηγής: api (Velocidrone Open API) > web > csv."""
    weekly = _get_weekly()
    if source in ("auto", "api") and weekly and weekly.get("track_id"):
        from velocidrone_api import fetch_leaderboard
        track_id = int(weekly["track_id"])
        race_mode = int(weekly.get("race_mode", 6))
        try:
            entries = fetch_leaderboard(track_id, race_mode=race_mode)
        except Exception as e:
            print(f"  ! API σφάλμα ({e}) - θα ξαναδοκιμάσει στην επόμενη σάρωση")
            return {}
        if entries:
            return {weekly["track"]: entries}
        print(f"  ! «{weekly['track']}»: κενό leaderboard")
        return {}
    use_web = source == "web" or (source == "auto" and (TRACK_URLS or SCENERY_IDS))
    if use_web:
        from velocidrone_web import load_all_tracks_web
        return load_all_tracks_web()
    return load_all_tracks(tracks_dir)


def _entry_key(entry: dict) -> str:
    """Μοναδικό κλειδί εγγραφής: πιλότος (+μοντέλο/model_id αν υπάρχει).
    Ο ίδιος πιλότος με διαφορετικά quads = ξεχωριστές εγγραφές."""
    model = entry.get("model") or entry.get("model_id")
    return f"{entry['pilot']}|{model}" if model is not None else entry["pilot"]


def _class_label(cls: str) -> str:
    try:
        from velocidrone_web import CLASS_LABELS
        return CLASS_LABELS.get(cls, cls)
    except ImportError:
        return cls


def announce_record(track, pilot, new_time, is_new_top, entries, cls=None, model=None):
    """Real-time ανακοίνωση νέου ρεκόρ με ποικιλία μηνυμάτων (engagement!)."""
    import random
    from messages import NEW_TOP, PERSONAL, CALL_TO_ACTION, pick

    category = get_category(track)
    category_label = themed_day_label(category) if category != "uncategorized" else ""
    cls_label = f"[{_class_label(cls)}] " if cls else ""

    base = pick(NEW_TOP if is_new_top else PERSONAL).format(
        pilot=f"**{pilot}**", track=track, time=new_time)
    if random.random() < 0.4:   # 40% πιθανότητα για κρεσέντα engagement
        base += "\n" + pick(CALL_TO_ACTION)

    from messages import GIF_NEW_TOP, GIF_PERSONAL
    pool = GIF_NEW_TOP if is_new_top else GIF_PERSONAL
    gif = None
    if pool:
        # Δικά σας GIFs (αν έχετε βάλει links) - 50% πιθανότητα
        if random.random() < 0.5:
            gif = pick(pool)
    else:
        # Αυτόματα GIF από Tenor - 50% πιθανότητα
        if random.random() < 0.5:
            from gif_fetcher import gif_for
            gif = gif_for("new_top" if is_new_top else "personal") or None

    send_discord_embed(
        title=f"{cls_label}«{track}» {category_label}".strip(),
        description=base,
        fields=format_leaderboard_discord_embed_fields(entries, top_n=TOP_N),
        image=gif,
    )


def _entry_key(entry: dict) -> str:
    """Μοναδικό κλειδί εγγραφής: πιλότος (+μοντέλο/model_id αν υπάρχει).
    Ο ίδιος πιλότος με διαφορετικά quads = ξεχωριστές εγγραφές."""
    model = entry.get("model") or entry.get("model_id")
    return f"{entry['pilot']}|{model}" if model is not None else entry["pilot"]


def _class_label(cls: str) -> str:
    try:
        from velocidrone_web import CLASS_LABELS
        return CLASS_LABELS.get(cls, cls)
    except ImportError:
        return cls


def announce_record(track, pilot, new_time, is_new_top, entries, cls=None, model=None):
    """Real-time ανακοίνωση νέου ρεκόρ με ποικιλία μηνυμάτων (engagement!)."""
    import random
    from messages import NEW_TOP, PERSONAL, CALL_TO_ACTION, pick

    category = get_category(track)
    category_label = themed_day_label(category) if category != "uncategorized" else ""
    cls_label = f"[{_class_label(cls)}] " if cls else ""
    model_txt = f" ({model})" if model else ""

    base = pick(NEW_TOP if is_new_top else PERSONAL).format(
        pilot=pilot, track=track, time=new_time)
    # 40% πιθανότητα για κρεσέντα
    if random.random() < 0.4:
        base = base + "\n" + pick(CALL_TO_ACTION)

    send_discord_embed(
        title=f"{cls_label}«{track}» {category_label}".strip() or track,
        description=base.replace("{pilot}", f"**{pilot}**").replace("{time}", f"**{new_time:.3f}s**") if False else base,
        fields=format_leaderboard_discord_embed_fields(entries, top_n=TOP_N),
    )


def scan_once(tracks_dir: str = TRACKS_DIR, source: str = "auto") -> None:
    state = db.load_state()
    today = datetime.date.today().isoformat()
    tracks = load_tracks(tracks_dir, source)

    if not tracks:
        print(f"[{datetime.datetime.now():%H:%M:%S}] Δεν βρέθηκαν CSV στο '{tracks_dir}'.")
    else:
        print(f"[{datetime.datetime.now():%H:%M:%S}] Σάρωση {len(tracks)} tracks...")

    from whitelist import filter_entries
    for track, entries in tracks.items():
        before = len(entries)
        entries = filter_entries(entries)
        if before != len(entries):
            print(f"  «{track}»: whitelist ενεργή ({len(entries)}/{before} εγγραφές είναι μέλη)")
        known = state["tracks"].get(track)
        if not known:
            # Πρώτο import του track -> σιωπηλή καταγραφή (όχι spam 15 posts μαζί)
            for e in entries:
                db.set_best(state, track, _entry_key(e), e["time"], e.get("class"))
            print(f"  + «{track}»: πρώτο import, {len(entries)} εγγραφές (σιωπηλό).")
            continue

        # Χωρισμός ανά κλάση (5inch/whoop) αν το source δίνει μοντέλα
        try:
            from velocidrone_source import split_by_class
            groups = split_by_class(entries) if any("class" in e for e in entries) else {None: entries}
        except ImportError:
            groups = {None: entries}

        improved = {}
        for entry in entries:
            pilot, t = entry["pilot"], entry["time"]
            cls = entry.get("class") or ""
            old = known.get(cls, {}).get(_entry_key(entry))
            if old is not None and t >= old:
                continue  # όχι βελτίωση

            group = groups.get(cls) or groups.get(None) or entries
            # κορυφαίο ρεκόρ = #1 ΜΕΣΑ στην κλάση του (5inch/whoop ξεχωριστά)
            is_new_top = bool(group) and group[0]["pilot"] == pilot and t <= group[0]["time"] + 1e-9
            announce_record(track, pilot, t, is_new_top, group, cls or None, entry.get("model"))
            db.set_best(state, track, _entry_key(entry), t, cls)
            db.log_record(state, pilot, track, t, today)
            update_duel_times(track_name=track, pilot_name=pilot, new_time=t)
            improved[cls] = improved.get(cls, 0) + 1

        # Teaser ΜΟΝΟ αν υπήρξε βελτίωση σε αυτή την κλάση αυτή τη σάρωση
        # (αλλιώς θα σπάμμαρε το ίδιο μήνυμα κάθε 5 λεπτά)
        from messages import TEASER, pick
        for cls, group in groups.items():
            if improved.get(cls or None) or improved.get(cls):
                teaser = proximity_teaser(group, templates=TEASER)
                if teaser:
                    send_discord_message(teaser)

        # Αυτόματες προτάσεις duels (ντέρμπι που κρατούν μέρες)
        from duel_suggestions import update_suggestions
        from messages import DUEL_SUGGEST
        for s in update_suggestions(track, groups):
            send_discord_message(pick(DUEL_SUGGEST).format(**s))

    db.save_state(state)

    # Daily extras (duels που έληξαν) - ακίνδυνο να τρέχει σε κάθε σάρωση
    for announcement in check_expired_duels():
        send_discord_message(announcement)


def main() -> None:
    parser = argparse.ArgumentParser(description="Velocidrone -> Discord leaderboard bot")
    parser.add_argument("--once", action="store_true", help="μία σάρωση και τέλος")
    parser.add_argument("--loop", type=int, metavar="SECONDS",
                        help="συνεχές polling κάθε N δευτερόλεπτα")
    parser.add_argument("--demo", action="store_true",
                        help="χρήση των demo_data αντί για TRACKS_DIR")
    parser.add_argument("--source", choices=["auto", "web", "csv"], default="auto",
                        help="πηγή δεδομένων (default: auto)")
    args = parser.parse_args()

    tracks_dir = "demo_data" if args.demo else TRACKS_DIR

    if args.loop and not args.once:
        print(f"Polling κάθε {args.loop}s από '{tracks_dir}' [{args.source}] (Ctrl+C για τερματισμό)")
        try:
            while True:
                scan_once(tracks_dir, args.source)
                time.sleep(args.loop)
        except KeyboardInterrupt:
            print("Τερματισμός.")
    else:
        scan_once(tracks_dir, args.source)


if __name__ == "__main__":
    main()
