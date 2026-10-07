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
    return g.get("images", {}).get("original", {}).get("url", "")


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


def fetch_gif(query: str) -> str:
    """URL τυχαίου GIF ή "" αν αποτύχουν όλα."""
    for fn in (
        lambda: _from_giphy(query, GIPHY_KEY) if GIPHY_KEY else None,
        lambda: _from_giphy(query, GIPHY_DEMO),
        lambda: _from_tenor(query),
    ):
        try:
            url = fn()
            if url:
                return url
        except Exception:
            continue
    return ""


# Έτοιμα query-sets ανά event
QUERIES_NEW_TOP = ["fpv drone racing", "drone fast fly", "speedometer fast", "rocket launch"]
QUERIES_PERSONAL = ["fpv drone", "drone flying", "quadcopter"]
QUERIES_RACE_FINISH = ["race flag win", "victory celebration", "champion"]
QUERIES_DUEL = ["versus fight", "boxing match", "epic battle"]
QUERIES_TEASER = ["close race", "neck and neck", "drone chase"]
QUERIES_WEEK = ["new adventure begin", "race track start", "fpv freestyle"]
QUERIES_RACE_START = ["race start lights", "green light go", "engines start"]


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
