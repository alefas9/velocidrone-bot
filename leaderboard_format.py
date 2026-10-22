"""
leaderboard_format.py

Δύο δουλειές:
1. Μορφοποιεί το leaderboard με emojis (medal για top-3, ranking για τους υπόλοιπους)
2. Υπολογίζει το "teaser" μήνυμα -> πόσο κοντά είναι κάποιος στο #1

Δεν χρειάζεται καμία νέα βιβλιοθήκη - μόνο python builtin.
"""
from __future__ import annotations

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def format_leaderboard(entries: list, top_n: int = 10) -> str:
    """
    :param entries: λίστα από dicts, ταξινομημένη ήδη κατά ranking, π.χ.
        [{"pilot": "Nikos", "time": 58.342}, {"pilot": "Maria", "time": 58.901}, ...]
    :param top_n: πόσες θέσεις να δείξει
    :return: string έτοιμο για post (λειτουργεί και σε Discord και σε Telegram - χρησιμοποιεί
             μόνο emoji + plain text, όχι HTML tags)
    """
    lines = []
    for i, entry in enumerate(entries[:top_n], start=1):
        marker = MEDALS.get(i, f"{i}.")
        lines.append(f"{marker}  {entry['pilot']}  —  {entry['time']:.3f}s")
    return "\n".join(lines)


def format_leaderboard_discord_embed_fields(entries: list, top_n: int = 10) -> list:
    """Εναλλακτική μορφή, έτοιμη για χρήση σε send_discord_embed(fields=...)."""
    fields = []
    for i, entry in enumerate(entries[:top_n], start=1):
        marker = MEDALS.get(i, f"#{i}")
        fields.append({
            "name": f"{marker} {entry['pilot']}",
            "value": f"{entry['time']:.3f}s",
            "inline": True,
        })
    return fields


def _format_teaser(leader, chaser, gap, leader_rank, templates, mm):
    """Ένα teaser μήνυμα για ζευγάρι leader/chaser (με tag αν υπάρχει id)."""
    chaser_name = chaser["pilot"]
    chaser_id = (mm or {}).get(chaser_name.lower())
    if templates:
        from messages import pick
        text = pick(templates).format(
            chaser=chaser_name, leader=leader["pilot"],
            gap=gap, pos=leader_rank, track="")
    elif leader_rank == 1:
        text = f"⚡ {chaser_name} χρειάζεται μόνο {gap:.3f}s για να πάρει το #1 από τον {leader['pilot']}!"
    else:
        text = f"⚡ {chaser_name} χρειάζεται μόνο {gap:.3f}s για να προσπεράσει τον {leader['pilot']} (θέση #{leader_rank})!"
    if chaser_id:
        text = text.replace(chaser_name, f"<@{chaser_id}>", 1)
    return text, chaser_id, f"{leader['pilot']}|{chaser_name}"


def proximity_teasers(entries: list, chaser_rank_threshold: int = 5,
                      templates: list | None = None, mm: dict = None,
                      max_teasers: int = 2) -> list:
    """ΟΛΕΣ οι κοντινές μάχες στο top N (όχι μόνο η κορυφαία).

    Επιστρέφει λίστα από (text, chaser_id, key), ταξινομημένη κατά gap
    (οι πιο σφιχτές μάχες πρώτες), το πολύ `max_teasers` αποτελέσματα.
    """
    if not entries or len(entries) < 2:
        return []
    top = entries[:chaser_rank_threshold]
    THRESHOLD_SECONDS = 0.5   # μόνο "δραματικές" αποστάσεις
    battles = []
    for i in range(len(top) - 1):
        gap = top[i + 1]["time"] - top[i]["time"]
        if gap <= THRESHOLD_SECONDS:
            battles.append((gap, top[i], top[i + 1], i + 1))
    battles.sort(key=lambda b: b[0])
    return [_format_teaser(b[1], b[2], b[0], b[3], templates, mm)
            for b in battles[:max_teasers]]


def proximity_teaser(entries: list, chaser_rank_threshold: int = 5,
                       templates: list | None = None, mm: dict = None):
    """
    Πίσω συμβατότητα: μόνο η «καλύτερη» (πιο σφιχτή) μάχη.
    Επιστρέφει πάντα (text, chaser_id, key).
    """
    res = proximity_teasers(entries, chaser_rank_threshold, templates, mm, max_teasers=1)
    return res[0] if res else (None, None, None)
