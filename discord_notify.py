"""
discord_notify.py

Στέλνει μηνύματα και embeds σε Discord channel μέσω Webhook.
Αν δεν έχει οριστεί DISCORD_WEBHOOK_URL, τυπώνει στο console (χρήσιμο για testing).
"""
from __future__ import annotations

import requests

from config import DISCORD_WEBHOOK_URL

TIMEOUT = 10


def _post(payload: dict) -> None:
    if not DISCORD_WEBHOOK_URL:
        print("--- [DISCORD - δεν έχει οριστεί webhook, εκτύπωση] ---")
        print(payload.get("content") or payload.get("embeds"))
        print("--- [/DISCORD] ---")
        return
    r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()


def send_discord_message(text: str) -> None:
    """Απλό μήνυμα (μέχρι 2000 χαρακτήρες)."""
    for chunk in _chunks(text, 2000):
        _post({"content": chunk, "allowed_mentions": {"parse": []}})


def send_discord_embed(title: str, description: str = "", fields: list | None = None,
                       color: int = 0x2ECC71) -> None:
    """Rich embed message (title + description + fields όπως στο leaderboard)."""
    embed = {"title": title[:256], "color": color}
    if description:
        embed["description"] = description[:4096]
    if fields:
        embed["fields"] = fields[:25]
    _post({"embeds": [embed], "allowed_mentions": {"parse": []}})


def _chunks(text: str, size: int):
    while text:
        yield text[:size]
        text = text[size:]
