"""
health_check.py

Πλήρης έλεγχος υγείας του συστήματος. Τρέξε περιοδικά ή όποτε κάτι φαίνεται περίεργο:

  python3 health_check.py            # έλεγχος χωρίς Discord post
  python3 health_check.py --discord  # + δοκιμαστικό μήνυμα στο κανάλι

Επιστρέφει 0 αν όλα OK, 1 αν υπάρχει πρόβλημα.
"""

import json
import os
import sys

RESULTS = []


def check(name, ok, detail=""):
    mark = "✅" if ok else "❌"
    RESULTS.append(ok)
    print(f"{mark} {name}" + (f" — {detail}" if detail else ""))
    return ok


def main():
    print("=" * 50)
    print("🩺 FPV BOT — HEALTH CHECK")
    print("=" * 50)

    # 1. .env / webhook
    from config import DISCORD_WEBHOOK_URL
    check("Discord webhook ρυθμισμένο", bool(DISCORD_WEBHOOK_URL),
          "στο .env" if DISCORD_WEBHOOK_URL else "ΛΕΙΠΕΙ το DISCORD_WEBHOOK_URL!")

    # 2. whitelist
    import whitelist
    wl = whitelist.load()
    check("Whitelist", True, f"{len(wl)} μέλη" + (" (ενεργή)" if wl else " (ΑΝΕΝΕΡΓΗ - βλέπει όλους)"))

    # 3. πίστα εβδομάδας
    weekly = {}
    if os.path.exists("weekly_track.json"):
        with open("weekly_track.json", encoding="utf-8") as f:
            weekly = json.load(f)
    check("Πίστα εβδομάδας", bool(weekly.get("track_id")),
          f"«{weekly.get('track')}» id={weekly.get('track_id')}" if weekly.get("track_id") else "ΔΕΝ έχει οριστεί")

    # 4. API fetch (live!)
    if weekly.get("track_id"):
        try:
            import velocidrone_api as va
            entries = va.fetch_leaderboard(int(weekly["track_id"]),
                                           race_mode=int(weekly.get("race_mode", 6)))
            check("Velocidrone API", True, f"{len(entries)} εγγραφές στη «{weekly['track']}»")
        except Exception as e:
            check("Velocidrone API", False, f"σφάλμα: {e}")
    else:
        check("Velocidrone API", False, "παράλειψη (δεν υπάρχει πίστα)")

    # 5. state
    import db
    state = db.load_state()
    n_tracks = len(state.get("tracks", {}))
    n_entries = sum(len(e) for t in state.get("tracks", {}).values()
                    for e in t.values())
    check("State (ιστορικό χρόνων)", n_entries > 0,
          f"{n_entries} εγγραφές σε {n_tracks} tracks")

    # 6. classes (μόνο 5inch/whoop)
    classes = {c for t in state.get("tracks", {}).values() for c in t}
    odd = classes - {"5inch", "whoop"}
    check("Κλάσεις καθαρές (5inch/whoop)", not odd,
          f"{sorted(classes)}" + (f" ⚠️ περίεργες: {sorted(odd)}" if odd else ""))

    # 7. model classes
    import velocidrone_api as va2
    mc = va2.load_model_classes()
    check("Χάρτης μοντέλων", True, f"{len(mc)} model_ids χαρτογραφημένα")

    # 8. standings
    import points
    st = points.load_standings()
    n_pilots = sum(len(v) for v in st.get("classes", {}).values())
    check("Βαθμολογία σεζόν", True,
          f"{n_pilots} πιλότοι" if n_pilots else "κενή (θα γεμίσει στην πρώτη αλλαγή πίστας)")

    # 9. git (pull/push δυνατότητα)
    r = os.popen("git remote get-url origin 2>/dev/null").read().strip()
    check("Git remote", bool(r), "με token ✓" if "github_pat_" in r else "ΧΩΡΙΣ token (push θα αποτύχει)")
    os.popen("git fetch origin 2>/dev/null").read()
    local = os.popen("git rev-parse HEAD 2>/dev/null").read().strip()
    remote = os.popen("git rev-parse origin/main 2>/dev/null").read().strip()
    if local and remote:
        check("Git σε συγχρονισμό", local == remote,
              "εντάξει" if local == remote else "ΤΟΠΙΚΑ ΠΙΣΩ - τρέξε git pull")
    else:
        check("Git σε συγχρονισμό", False, "δεν διαβάστηκε HEAD")

    # 10. site_data.json
    if os.path.exists("site_data.json"):
        age = (json.load(open("site_data.json")).get("generated_at", ""))
        check("site_data.json", True, f"υπάρχει (created {age[:16]})")
    else:
        check("site_data.json", False, "ΛΕΙΠΕΙ - τρέξε export_site_data.py")

    # 11. tasks (παρουσία σημαντικών αρχείων)
    for f in ["update_leaderboard.py", "velocidrone_api.py", "messages.py",
              "whitelist.py", "points.py", "export_site_data.py", "duel_suggestions.py"]:
        check(f"Αρχείο {f}", os.path.exists(f))

    print("=" * 50)
    failed = RESULTS.count(False)
    if failed == 0:
        print("🎉 ΟΛΑ OK — το σύστημα είναι υγιές!")
    else:
        print(f"⚠️  {failed} πρόβλημα(τα) παραπάνω — πες τα μου!")
    print("=" * 50)

    if "--discord" in sys.argv and not failed:
        from discord_notify import send_discord_message
        send_discord_message("🩺 Health check: ΟΛΑ ΟΚ! Το σύστημα τρέχει ρολόι. 🏁")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
