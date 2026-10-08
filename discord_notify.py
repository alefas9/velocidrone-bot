"""
discord_notify.py

Στέλνει μηνύματα και embeds σε Discord channel μέσω Webhook.
Αν δεν έχει οριστεί DISCORD_WEBHOOK_URL, τυπώνει στο console (χρήσιμο για testing).
"""
from __future__ import annotations

import requests

from config import DISCORD_WEBHOOK_URL, DISCORD_WEBHOOK_ADMIN_URL

TIMEOUT = 10


def _mentions(mentions: list | None) -> dict:
    """allowed_mentions: ping μόνο στα συγκεκριμένα user IDs (ή τίποτα)."""
    if mentions:
        return {"users": [str(m) for m in mentions]}
    return {"parse": []}


def _post(payload: dict) -> None:
    # debug: καταγραφή image/GIF που στέλνεται
    for e in payload.get("embeds", []):
        if e.get("image"):
            print(f"[dn] EMBED IMAGE -> {e['image']['url'][:90]}")
    if not DISCORD_WEBHOOK_URL:
        print("--- [DISCORD - δεν έχει οριστεί webhook, εκτύπωση] ---")
        print(payload.get("content") or payload.get("embeds"))
        print("--- [/DISCORD] ---")
        return
    r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()


def send_discord_message(text: str, mentions: list | None = None) -> None:
    """Απλό μήνυμα (μέχρι 2000 χαρακτήρες).
    mentions: λίστα Discord user IDs για ping (<@ID>)."""
    for chunk in _chunks(text, 2000):
        _post({"content": chunk, "allowed_mentions": _mentions(mentions)})


def send_discord_embed(title: str, description: str = "", fields: list | None = None,
                       color: int = 0x2ECC71, image: str | None = None,
                       mentions: list | None = None) -> None:
    """Rich embed message (title + description + fields όπως στο leaderboard).
    image: URL εικόνας/GIF που εμφανίζεται μεγάλη κάτω από το embed.
    mentions: λίστα Discord user IDs για ping (<@ID>)."""
    embed = {"title": title[:256], "color": color}
    if description:
        embed["description"] = description[:4096]
    if fields:
        embed["fields"] = fields[:25]
    payload = {"embeds": [embed], "allowed_mentions": _mentions(mentions)}
    if image:
        # ΠΑΝΤΑ σαν content link: το Discord κάνει unfurl και παίζει το GIF
        # σίγουρα (τα URLs της Giphy δεν τελειώνουν σε .gif πάντα, οπότε
        # ο έλεγχος endswith χαλούσε το embed rendering).
        payload["content"] = image
    _post(payload)


def send_discord_admin_message(text: str) -> None:
    """Μήνυμα στο admin κανάλι (alerts/watchdog). Αν δεν έχει οριστεί,
    πέφτει πίσω στο κανονικό webhook."""
    global DISCORD_WEBHOOK_URL
    if DISCORD_WEBHOOK_ADMIN_URL:
        original, DISCORD_WEBHOOK_URL = DISCORD_WEBHOOK_URL, DISCORD_WEBHOOK_ADMIN_URL
        try:
            send_discord_message(text)
        finally:
            DISCORD_WEBHOOK_URL = original
    else:
        send_discord_message(text)


def send_discord_admin_embed(title: str, description: str = "", fields: list | None = None,
                             color: int = 0x2ECC71, image: str | None = None) -> None:
    """Embed στο admin κανάλι (fallback: κανονικό)."""
    global DISCORD_WEBHOOK_URL
    if DISCORD_WEBHOOK_ADMIN_URL:
        original, DISCORD_WEBHOOK_URL = DISCORD_WEBHOOK_URL, DISCORD_WEBHOOK_ADMIN_URL
        try:
            send_discord_embed(title=title, description=description, fields=fields,
                               color=color, image=image)
        finally:
            DISCORD_WEBHOOK_URL = original
    else:
        send_discord_embed(title=title, description=description, fields=fields,
                           color=color, image=image)


def _chunks(text: str, size: int):
    while text:
        yield text[:size]
        text = text[size:]
