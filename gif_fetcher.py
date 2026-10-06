"""
gif_fetcher.py

Αυτόματη αναζήτηση GIF από Tenor (η πλατφόρμα που χρησιμοποιεί και το Discord).
Καλείται μόνο όταν πρόκειται να ποσταριστεί ανακοίνωση - όχι σε κάθε σάρωση.

Αν κάποια στιγμή το δημόσιο demo key σταματήσει να δουλεύει:
  1. Πήγαινε στο https://tenor.com/gifapi (δωρεάν, 2 λεπτά)
  2. Πάρε δικό σου key
  3. Βάλ' το στο .env:  TENOR_API_KEY=το_κλειδι_σου
"""

import os
import random

import requests

# Δημόσιο demo key του Tenor (λειτουργεί χωρίς εγγραφή - αν σταματήσει, βλ. παραπάνω)
TENOR_KEY = os.environ.get("TENOR_API_KEY", "LIVDSRZULELA")
TENOR_URL = "https://api.tenor.com/v1/search"


def fetch_gif(query: str) -> str:
    """Επιστρέφει URL τυχαίου GIF για το query, ή "" αν αποτύχει (χάρις)."""
    try:
        r = requests.get(TENOR_URL, params={
            "q": query, "key": TENOR_KEY, "limit": 20,
            "media_filter": "minimal",
        }, timeout=8)
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            return ""
        g = random.choice(results)
        # content_url = απευθείας σύνδεσμος GIF
        return g.get("content_url") or g.get("media", [{}])[0].get("gif", {}).get("url", "")
    except Exception:
        return ""   # καμία ενημέρωση δεν αξίζει να χαλάσει ένα post


# Έτοιμα query-sets ανά event (mix για ποικιλία)
QUERIES_NEW_TOP = ["fpv drone racing", "drone fast fly", "speedometer fast", "rocket launch"]
QUERIES_PERSONAL = ["fpv drone", "drone flying", "quadcopter"]
QUERIES_RACE_FINISH = ["race flag win", "victory celebration", "champion"]
QUERIES_DUEL = ["versus fight", "boxing match", "epic battle"]


def gif_for(category: str) -> str:
    """Τυχαίο GIF για την κατηγορία. Κενό string αν δεν βρεθεί/αποτύχει."""
    queries = {
        "new_top": QUERIES_NEW_TOP,
        "personal": QUERIES_PERSONAL,
        "race_finish": QUERIES_RACE_FINISH,
        "duel": QUERIES_DUEL,
    }.get(category, QUERIES_PERSONAL)
    return fetch_gif(random.choice(queries))
