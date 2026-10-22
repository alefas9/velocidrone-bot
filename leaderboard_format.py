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


def proximity_teaser(entries: list, chaser_rank_threshold: int = 5,
                       templates: list | None = None, mm: dict = None):
    """
    Ελέγχει αν κάποιος μέσα στις πρώτες `chaser_rank_threshold` θέσεις είναι πολύ κοντά
    στον επόμενο από πάνω του, και επιστρέφει ένα "teaser" μήνυμα.

    Επιστρέφει πάντα (text, chaser_id, key):
      text      -> το μήνυμα (ή None αν δεν υπάρχει αρκετά κοντινή μάχη)
      chaser_id -> Discord user id του κυνηγού (μέσω mention_map mm) ή None
      key       -> "leader|chaser" (για cooldown/αποφυγή spam στα tags)

    Με mm, το όνομα του κυνηγού γίνεται <@id> στο κείμενο - πέρασέ το ως
    mentions=[chaser_id] στην αποστολή για να κάνει ping.

    Λογική: ψάχνει τη ΜΙΚΡΟΤΕΡΗ διαφορά ανάμεσα σε δύο διαδοχικές θέσεις μέσα στο top N,
    και αν είναι κάτω από ένα κατώφλι (π.χ. 0.5s), το αναδεικνύει.
    """
    if len(entries) < 2:
        return None

    best_gap = None
    best_pair = None

    for i in range(min(chaser_rank_threshold, len(entries) - 1)):
        leader = entries[i]
        chaser = entries[i + 1]
        gap = chaser["time"] - leader["time"]
        if best_gap is None or gap < best_gap:
            best_gap = gap
            best_pair = (leader, chaser, i + 1)  # i+1 = η θέση του leader (1-based)

    if best_gap is None:
        return None, None, None

    # Κατώφλι: μόνο αν η διαφορά είναι "δραματική" (προσάρμοσέ το όπως θες)
    THRESHOLD_SECONDS = 0.5
    if best_gap > THRESHOLD_SECONDS:
        return None, None, None

    leader, chaser, leader_rank = best_pair
    chaser_name = chaser["pilot"]
    chaser_id = (mm or {}).get(chaser_name.lower())
    if templates:
        from messages import pick
        text = pick(templates).format(
            chaser=chaser_name, leader=leader["pilot"],
            gap=best_gap, pos=leader_rank, track="")
    elif leader_rank == 1:
        text = f"⚡ {chaser_name} χρειάζεται μόνο {best_gap:.3f}s για να πάρει το #1 από τον/την {leader['pilot']}!"
    else:
        text = f"⚡ {chaser_name} χρειάζεται μόνο {best_gap:.3f}s για να προσπεράσει τον/την {leader['pilot']} (θέση #{leader_rank})!"
    if chaser_id:
        text = text.replace(chaser_name, f"<@{chaser_id}>", 1)
    return text, chaser_id, f"{leader['pilot']}|{chaser_name}"
