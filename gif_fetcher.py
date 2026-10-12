"""
gif_fetcher.py

Αυτόματη αναζήτηση GIF. Σειρά προσπάθειας:
  1. Giphy API (με δικό σου δωρεάν key -> το καλύτερο, 2 λεπτά εγγραφή)
  2. Giphy public demo key (δουλεύει συνήθως)
  3. Tenor demo key (legacy - συχνά κομμένο)

ΠΩΣ ΠΑΙΡΝΕΙΣ ΔΙΚΟ ΣΟΥ KEY (συνιστάται - σιγουριά 100%):
  1. https://developers.giphy.com → "Create an App" → βάλε όνομα (π.χ. fpv-bot)
     -> παίρνεις API key ΑΜΕΣΩΣ (δωρεάν, χωρίς έγκριση)
  2. Στο .env του NAS πρόσθεσε:   GIPHY_API_KEY=το_key_σου

Αν όλα αποτύχουν -> κενό string (το post βγαίνει κανονικά χωρίς GIF).
"""
from __future__ import annotations

import os
import random

import requests

GIPHY_KEY = os.environ.get("GIPHY_API_KEY", "")
GIPHY_DEMO = "dc6zaTOxFJmzC"           # public beta key
TENOR_KEY = os.environ.get("TENOR_API_KEY", "LIVDSRZULELA")


def _from_giphy(query: str, key: str) -> str:
    r = requests.get("https://api.giphy.com/v1/gifs/search", params={
        "api_key": key, "q": query, "limit": 25, "rating": "pg",
    }, timeout=8)
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data:
        return ""
    g = random.choice(data)
    # Σημαντικό: επιστρέφουμε το LINK ΣΕΛΙΔΑΣ (giphy.com/gifs/...) και ΟΧΙ
    # το media/v1.Y2lk URL - το Discord κάνει unfurl τα page links και
    # παίζει το GIF, ενώ τα νέα media URLs δεν τα render-άρει.
    return g.get("url") or g.get("bitly_url") or g.get("images", {}).get("original", {}).get("url", "")


def _from_tenor(query: str) -> str:
    r = requests.get("https://api.tenor.com/v1/search", params={
        "q": query, "key": TENOR_KEY, "limit": 20,
    }, timeout=8)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return ""
    g = random.choice(results)
    return g.get("content_url", "")


def fetch_gif_full(query: str) -> dict | None:
    """{'page': link_σελίδας, 'media': απευθείας_URL_για_download} ή None."""
    try:
        key = GIPHY_KEY or GIPHY_DEMO
        r = requests.get("https://api.giphy.com/v1/gifs/search", params={
            "api_key": key, "q": query, "limit": 25, "rating": "pg",
        }, timeout=8)
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            return None
        gif = random.choice(data)
        imgs = gif.get("images", {})
        media = (imgs.get("downsized", {}).get("url")
                 or imgs.get("fixed_height", {}).get("url")
                 or imgs.get("original", {}).get("url"))
        page = gif.get("url") or media
        if page or media:
            return {"page": page, "media": media}
    except Exception:
        pass
    return None


def fetch_gif(query: str) -> str:
    """URL τυχαίου GIF ή "" αν αποτύχουν όλα."""
    info = fetch_gif_full(query)
    return (info or {}).get("page", "")


# Έτοιμα query-sets ανά event (ποικιλία: κάθε query = διαφορετική δεξαμενή GIF)
QUERIES_NEW_TOP = [
    "fpv drone racing", "drone fast fly", "speedometer fast", "rocket launch",
    "hyperspace jump", "lightning fast", "jet afterburner", "drone acro",
    "top speed", "supersonic",
]
QUERIES_PERSONAL = [
    "fpv drone", "drone flying", "quadcopter", "drone freestyle",
    "drone pilot view", "mini drone fpv", "drone cinematic", "propeller spin",
]
QUERIES_RACE_FINISH = [
    "race flag win", "victory celebration", "champion", "checkered flag",
    "confetti win", "podium celebration", "gold medal", "raise the roof",
]
QUERIES_DUEL = [
    "versus fight", "boxing match", "epic battle", "head to head",
    "face off", "mortal combat", "sword duel", "final showdown",
]
QUERIES_TEASER = [
    "close race", "neck and neck", "drone chase", "photo finish",
    "so close", "almost there", "catch me if you can", "tight battle",
]
QUERIES_WEEK = [
    "new adventure begin", "race track start", "fpv freestyle", "new chapter",
    "fresh start", "level up", "on your marks", "game on",
]
QUERIES_RACE_START = [
    "race start lights", "green light go", "engines start", "countdown launch",
    "ready set go", "lights out and away we go", "start your engines",
]


def gif_for(category: str) -> str:
    queries = {
        "new_top": QUERIES_NEW_TOP,
        "personal": QUERIES_PERSONAL,
        "race_finish": QUERIES_RACE_FINISH,
        "duel": QUERIES_DUEL,
        "teaser": QUERIES_TEASER,
        "week": QUERIES_WEEK,
        "race_start": QUERIES_RACE_START,
    }.get(category, QUERIES_PERSONAL)
    return fetch_gif(random.choice(queries))
