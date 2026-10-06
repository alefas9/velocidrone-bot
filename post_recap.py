"""
post_recap.py

Ανασκόπηση/ρεπορτάζ της τρέχουσας εβδομάδας -> Discord.
Τρέξε μέσω Task Scheduler 2 φορές/εβδομάδα (π.χ. Τετάρτη + Κυριακή 21:00):

  python3 post_recap.py

Δείχνει: τρέχον leaderboard (top 10, με διαφορές), στατιστικά εβδομάδας
(πιο ενεργός πιλότης, μεγαλύτερη βελτίωση) και τη βαθμολογία σεζόν αν υπάρχει.
"""

import json
import os
import random
from collections import Counter
from datetime import datetime

import db
import points
from config import WEEKLY_TRACK_FILE
from discord_notify import send_discord_embed, send_discord_message
from messages import pick

RECAP_TITLES = [
    "📊 ΑΝΑΣΚΟΠΗΣΗ ΕΒΔΟΜΑΔΑΣ",
    "📺 ΡΕΠΟΡΤΑΖ ΑΓΩΝΙΣΤΙΚΗΣ",
    "📰 ΤΑ ΝΕΑ ΤΗΣ ΠΙΣΤΑΣ",
    "🎬 ΕΝΔΙΑΜΕΣΟ ΣΗΜΕΙΩΜΑ",
]


def main() -> None:
    # τρέχουσα πίστα
    weekly = {}
    if os.path.exists(WEEKLY_TRACK_FILE):
        with open(WEEKLY_TRACK_FILE, encoding="utf-8") as f:
            weekly = json.load(f)
    track = weekly.get("track")
    if not track:
        print("Δεν έχει οριστεί πίστα εβδομάδας - παράλειψη recap.")
        return

    state = db.load_state()
    classes = state.get("tracks", {}).get(track, {})
    if not classes:
        print("Δεν υπάρχουν δεδομένα για ανασκόπηση.")
        return

    best_overall = {}
    for cls, entries in classes.items():
        for key, t in entries.items():
            pilot = key.split("|")[0]
            if pilot not in best_overall or t < best_overall[pilot]:
                best_overall[pilot] = t

    ranked = sorted(best_overall.items(), key=lambda kv: kv[1])
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    leader_time = ranked[0][1]

    lines = []
    for i, (pilot, t) in enumerate(ranked[:10]):
        gap = t - leader_time
        gap_txt = "" if i == 0 else f"  (+{gap:.3f}s)"
        lines.append(f"{medals.get(i, f'**{i+1}.**')} **{pilot}**  {t:.3f}s{gap_txt}")
    if len(ranked) > 10:
        lines.append(f"...κι άλλοι {len(ranked)-10} πιλότοι στο κυνήγι!")

    # στατιστικά εβδομάδας από το records_log
    week_records = state.get("records_log", [])[-500:]
    stats_txt = ""
    if week_records:
        counts = Counter(r["pilot"] for r in week_records)
        most_active, n = counts.most_common(1)[0]
        stats_txt = f"\n\n📈 **Εβδομαδιαία στατιστικά:** {n} νέα ρεκόρ συνολικά - πιο ενεργός ο **{most_active}** ({counts[most_active]})."

    # GIF συνοδεία (50%) - θέματα ρεπορτάζ/νέων
    gif = None
    if random.random() < 0.5:
        from gif_fetcher import fetch_gif
        gif = fetch_gif(random.choice([
            "news broadcast", "tv report", "breaking news",
            "chart going up", "racing podium", "fpv drone",
        ])) or None

    send_discord_embed(
        title=f"{pick(RECAP_TITLES)} — «{track}»",
        description="\n".join(lines) + stats_txt,
        color=0x9B59B6,
        image=gif,
    )

    # βαθμολογία σεζόν (αν έχει ξεκινήσει)
    st = points.load_standings()
    for cls, pilots in st.get("classes", {}).items():
        if not pilots:
            continue
        season = sorted(pilots.items(), key=lambda kv: -kv[1]["points"])[:5]
        slines = [f"{medals.get(i, f'**{i+1}.**')} {p} — **{d['points']}** πόντοι"
                  for i, (p, d) in enumerate(season)]
        send_discord_embed(
            title=f"🏆 Βαθμολογία σεζόν [{cls}]",
            description="\n".join(slines),
            color=0x3498DB,
        )

    print(f"Recap posted for «{track}» ({len(ranked)} πιλότοι)")


if __name__ == "__main__":
    main()
