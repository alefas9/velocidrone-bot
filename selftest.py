"""
selftest.py

Αυτόματο τεστ συστήματος - τρέχει σε ΠΡΟΣΩΡΙΝΟ φάκελο (δεν αγγίζει τα
πραγματικά state files). Ιδανικό μετά από κάθε update.

Χρήση (στον φάκελο του bot):
    python3 selftest.py

Ελέγχει:
  A. imports όλων των modules
  B. καλωσόρισμα νέου πιλότου (μόνο ο νεοφερμένος, μία φορά)
  C. όχι-επανάληψη καλωσορίσματος στη 2η σάρωση
  D. Πιλότος της Εβδομάδας (υπολογισμός βελτίωσης)
  E. idempotency απονομής πόντων
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTS = []


def check(name: str, ok: bool, detail: str = ""):
    RESULTS.append((name, ok, detail))
    print(f"  {'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    td = tempfile.mkdtemp(prefix="fpv-selftest-")
    # αντιγραφή κώδικα στον προσωρινό φάκελο
    for f in os.listdir(BASE):
        if f.endswith(".py"):
            shutil.copy(os.path.join(BASE, f), td)
    os.mkdir(os.path.join(td, "tracks"))
    sys.path.insert(0, td)
    os.chdir(td)   # ΚΡΙΣΙΜΟ: όλα τα relative paths (state/standings) -> μόνο στο temp!

    print("A. Imports...")
    try:
        import db, points, messages, whitelist  # noqa
        import update_leaderboard  # noqa
        check("imports modules", True)
    except Exception as e:
        check("imports modules", False, str(e))

    print("B. Καλωσόρισμα νέου πιλότου...")
    open(os.path.join(td, "state.json"), "w").write(json.dumps({
        "tracks": {
            "OldTrack": {"5inch": {"Kostas|108": 70.0}},
            "TestTrack": {"5inch": {"Nikos|55": 60.0}}},
        "records_log": [], "welcomed": []}))
    open(os.path.join(td, "weekly_track.json"), "w").write(json.dumps(
        {"track": "TestTrack", "url": "https://www.velocidrone.com/leaderboard/1"}))
    open(os.path.join(td, "tracks", "TestTrack.csv"), "w").write(
        "Position,Name,Time\n1,Nikos,59.5\n2,Giannis,65.0\n")
    r = subprocess.run([sys.executable, "update_leaderboard.py", "--once", "--source", "csv"],
                       cwd=td, capture_output=True, text=True)
    # σημείωση: κάποια templates έχουν 🆕 στο κείμενο - ψάχνουμε τη γραμμή log
    welcomes = [l for l in r.stdout.splitlines() if "Καλωσόρισμα νέου πιλότου" in l]
    check("μόνο ο νεοφερμένος καλωσορίζεται",
          len(welcomes) == 1 and "Giannis" in welcomes[0],
          f"{len(welcomes)} welcome(s)")
    st = json.load(open(os.path.join(td, "state.json")))
    check("welcomed αποθηκεύτηκε", st.get("welcomed") == ["Giannis"],
          str(st.get("welcomed")))

    print("C. Όχι επανάληψη καλωσορίσματος...")
    r = subprocess.run([sys.executable, "update_leaderboard.py", "--once", "--source", "csv"],
                       cwd=td, capture_output=True, text=True)
    check("2η σάρωση σιωπηλή", "Καλωσόρισμα νέου πιλότου" not in r.stdout)

    print("D. Πιλότος της Εβδομάδας...")
    open(os.path.join(td, "state.json"), "w").write(json.dumps({
        "tracks": {
            "Week1": {"5inch": {"Nikos|55": 65.0, "Maria|59": 62.0}},
            "Week2": {"5inch": {"Nikos|55": 58.5, "Maria|59": 63.0}}},
        "records_log": [], "welcomed": []}))
    import importlib
    for m in ("db", "points"):
        if m in sys.modules:
            del sys.modules[m]
    import db, points
    potw = points.pilot_of_the_week(db.load_state(), "Week2", "Week1")
    check("POTW = Nikas +10%", potw and potw[0] == "Nikos" and abs(potw[1] - 10.0) < 0.01,
          str(potw))

    print("F. Κλοπή κορυφής (crown theft)...")
    for m in ("update_leaderboard", "messages", "gif_fetcher"):
        if m in sys.modules:
            del sys.modules[m]
    import update_leaderboard as ul
    captured = {}

    def _fake_embed(title=None, description=None, **kw):
        captured["desc"] = description or ""

    ul.send_discord_embed = _fake_embed
    import gif_fetcher
    gif_fetcher.fetch_gif_full = lambda q: None   # χωρίς GIF/δίκτυο
    ul.announce_record("Week2", "ZOUP", 59.5, True,
                       [{"pilot": "ZOUP", "time": 59.5}],
                       cls="5inch", stolen_from="Nikos")
    check("μήνυμα κλοπής αναφέρει τον προηγούμενο leader",
          "Nikos" in captured.get("desc", ""),
          captured.get("desc", "")[:70])
    ul.announce_record("Week2", "ZOUP", 59.0, True,
                       [{"pilot": "ZOUP", "time": 59.0}],
                       cls="5inch", stolen_from=None)
    check("κανονικό new top χωρίς κλοπή",
          "Nikos" not in captured.get("desc", ""),
          captured.get("desc", "")[:70])

    print("E. Idempotency απονομής...")
    open(os.path.join(td, "state.json"), "w").write(json.dumps({
        "tracks": {"WT": {"5inch": {"A|1": 60.0, "B|2": 61.0}}},
        "records_log": []}))
    if "points" in sys.modules:
        del sys.modules["points"]
    import points as pts
    s = db.load_state()
    r1 = pts.award_week("WT", s)
    pts.save_standings(pts.load_standings())
    r2 = pts.award_week("WT", db.load_state())
    check("2η απονομή κόβεται", len(r1) == 1 and r2 == [])

    shutil.rmtree(td, ignore_errors=True)
    failed = [n for n, ok, _ in RESULTS if not ok]
    print()
    if failed:
        print(f"❌ ΑΠΟΤΥΧΙΕΣ: {failed}")
        return 1
    print(f"🎉 ΟΛΑ ΕΝΤΑΞΕΙ ({len(RESULTS)} ελέγχοι πέρασαν)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
