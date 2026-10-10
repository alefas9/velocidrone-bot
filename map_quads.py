"""
map_quads.py

ΑΥΤΟΜΑΤΗ χαρτογράφηση model_id -> όνομα quad.

Πηγές:
  - API (velocidrone_api): δίνει πιλότο + model_id για κάθε εγγραφή leaderboard
  - Website (velocidrone_web): δίνει πιλότο + ΟΝΟΜΑ μοντέλου για την ίδια εγγραφή

Ενώνοντας τις δύο πηγές ανά πιλότο, βγαίνει το mapping id->όνομα χωρίς
Fiddler και χωρίς να ρωτήσουμε κανέναν!

Χρήση (στο NAS, στον φάκελο του bot):
  python3 map_quads.py --track-id 39565 --name "SimRush Week1"
  python3 map_quads.py --track-id 39565 --url "https://www.velocidrone.com/leaderboard/39565"

Με --dry-run δείχνει τι θα έκανε χωρίς να γράψει τίποτα.
Με --force αντικαθιστά και ήδη υπάρχουσες καταχωρήσεις.
"""

import argparse
import sys

import quad_names
import velocidrone_api as va
import velocidrone_web as vw


def collect(track_id: int, url: str, name: str, race_mode: int):
    """Επιστρέφει (updates, ambiguous, stats) από τη σύγκριση API vs Website."""
    print(f"1/2 API leaderboard (track_id={track_id})...")
    api_entries = va.fetch_leaderboard(track_id, race_mode)
    if not api_entries:
        print("  ! το API δεν επέστρεψε εγγραφές - η πίστα δεν έχει χρόνους;")
        return {}, [], (0, 0)

    print(f"2/2 Website leaderboard ({url})...")
    web_entries = vw.fetch_track(name, url)
    if not web_entries:
        print("  ! το website δεν επέστρεψε εγγραφές - λάθος URL; δοκίμασε --url")
        return {}, [], (len(api_entries), 0)

    # ομαδοποίηση ανά πιλότο
    api_by_pilot = {}
    for e in api_entries:
        mid = e.get("model_id")
        if mid is not None:
            api_by_pilot.setdefault(e["pilot"], set()).add(str(mid))
    web_by_pilot = {}
    for e in web_entries:
        mdl = (e.get("model") or "").strip()
        if mdl:
            web_by_pilot.setdefault(e["pilot"], set()).add(mdl)

    updates, ambiguous = {}, []
    for pilot, ids in sorted(api_by_pilot.items()):
        names = web_by_pilot.get(pilot, set())
        if len(ids) == 1 and len(names) == 1:
            mid, mdl = next(iter(ids)), next(iter(names))
            updates[mid] = mdl
        else:
            # 0 ονόματα (πιλότος λείπει από web) ή πολλαπλά id/ονόματα
            if ids and names:
                ambiguous.append((pilot, sorted(ids), sorted(names)))

    stats = (len(api_by_pilot), len(web_by_pilot))
    return updates, ambiguous, stats


def main() -> None:
    p = argparse.ArgumentParser(description="Αυτόματη χαρτογράφηση model_id -> όνομα quad")
    p.add_argument("--track-id", type=int, required=True, help="π.χ. 39565")
    p.add_argument("--name", default="mapping",
                   help="όνομα πίστας (για μηνύματα)")
    p.add_argument("--url", default=None,
                   help="URL leaderboard στο website (default: /leaderboard/<track-id>)")
    p.add_argument("--race-mode", type=int, default=6)
    p.add_argument("--dry-run", action="store_true", help="χωρίς εγγραφή")
    p.add_argument("--force", action="store_true",
                   help="αντικατάσταση και ήδη υπαρχόντων καταχωρήσεων")
    args = p.parse_args()

    url = args.url or f"https://www.velocidrone.com/leaderboard/{args.track_id}"
    updates, ambiguous, (n_api, n_web) = collect(args.track_id, url,
                                                 args.name, args.race_mode)
    print(f"\nΠιλότοι: API={n_api}, Website={n_web}")

    if not updates and not ambiguous:
        print("Τίποτα προς χαρτογράφηση.")
        return

    existing = quad_names.load()
    new_entries, kept, conflicts = {}, {}, []
    for mid, mdl in updates.items():
        if mid in existing and existing[mid] == mdl:
            kept[mid] = mdl
        elif mid in existing and existing[mid] != mdl:
            conflicts.append((mid, existing[mid], mdl))
            if args.force:
                new_entries[mid] = mdl
        else:
            new_entries[mid] = mdl

    print(f"\n✓ Νέες χαρτογραφήσεις: {len(new_entries)}")
    for mid in sorted(new_entries, key=int):
        print(f"  {mid}: {new_entries[mid]}")
    if kept:
        print(f"= Ήδη ίδιες (αγνοήθηκαν): {len(kept)}")
    if conflicts:
        print(f"⚠ Διαφορές (κρατήθηκε η παλιά, --force για αντικατάσταση): {len(conflicts)}")
        for mid, old, new in conflicts:
            print(f"  {mid}: «{old}» vs «{new}»")
    if ambiguous:
        print(f"? Αμφίβολα (πολλαπλά quads ανά πιλότο - όρισε χειροκίνητα): {len(ambiguous)}")
        for pilot, ids, names in ambiguous:
            print(f"  {pilot}: ids={ids} names={names}")

    if args.dry_run:
        print("\n(dry-run - τίποτα δεν γράφτηκε)")
        return
    if new_entries:
        mapping = quad_names.load()
        mapping.update(new_entries)
        quad_names.save(mapping)
        print(f"\n💾 quad_names.json ενημερώθηκε (+{len(new_entries)})")
    else:
        print("\nquad_names.json αμετάβλητο.")


if __name__ == "__main__":
    main()
