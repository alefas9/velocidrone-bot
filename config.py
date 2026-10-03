"""
config.py

Κεντρικές ρυθμίσεις - διαβάζονται από environment variables (.env αρχείο).
Για απλότητα: φτιάξε ένα αρχείο .env δίπλα στα scripts και κάνε source, ή
τρέξε με:  DISCORD_WEBHOOK_URL=... python update_leaderboard.py --once
"""

import os


def _load_dotenv(path: str = ".env") -> None:
    """Ελάχιστος .env parser - χωρίς εξωτερική βιβλιοθήκη."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
TRACKS_DIR = os.environ.get("TRACKS_DIR", "./tracks").strip()
TOP_N = int(os.environ.get("TOP_N", "10"))
STATE_FILE = os.environ.get("STATE_FILE", "state.json")
DUELS_FILE = os.environ.get("DUELS_FILE", "duels.json")

# --- Web source (αυτόματο polling velocidrone.com) ---
# Μορφή: "Όνομα Track|https://www.velocidrone.com/leaderboard/...;Άλλο Track|https://..."
TRACK_URLS = os.environ.get("TRACK_URLS", "").strip()
# Προαιρετικό: ανακάλυψη tracks ανά scenery id (π.χ. "16,33" -> Empty Scene Day, Dynamic Weather)
SCENERY_IDS = [int(x) for x in os.environ.get("SCENERY_IDS", "").split(",") if x.strip()]
WEB_DELAY = float(os.environ.get("WEB_DELAY", "3"))        # δευτερόλεπτα μεταξύ requests
WEB_PAGES = int(os.environ.get("WEB_PAGES", "1"))          # πόσες σελίδες leaderboard
WEB_VERSION = os.environ.get("WEB_VERSION", "1.16")        # version string στα URLs
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "20"))
WEEKLY_TRACK_FILE = os.environ.get("WEEKLY_TRACK_FILE", "weekly_track.json")
