"""
velocidrone_api.py

ΠΗΓΗ ΜΕΛΛΟΝ: Velocidrone Open API με bearer token - ΠΛΗΡΩΣ ΑΥΤΟΜΑΤΟ
για ΟΛΕΣ τις πίστες συμπεριλαμβανομένων των community/custom.

Υπόθεση λειτουργίας (όπως το κάνει το FPVBattle - github.com/UaVelocidroneBattle/FPVBattle):
  - Ο χρήστης παίρνει bearer token από το velocidrone.com (profile / devs / FB group)
  - Το API επιστρέφει leaderboard ενός track σε JSON
  - Το bot το σκανάρει κάθε 5 λεπτά -> πλήρως αυτόματο, χωρίς CSV exports

ΚΑΤΑΣΤΑΣΗ: τα public docs του API δεν είναι δημοσιευμένα - αυτό το module
έχει probe mode για να ανακαλύψουμε τα endpoints όταν πάρουμε token:

  python3 velocidrone_api.py --probe <TRACK_ID>

Δοκιμάζει όλους τους πιθανούς συνδυασμούς base URL / path και τυπώνει τι απαντά
ο server (status code + πρώτα bytes) - από εκεί κλειδώνουμε το πραγματικό endpoint.
"""

import json
import os
import sys

import requests

from config import REQUEST_TIMEOUT

TOKEN = os.environ.get("VELOCIDRONE_TOKEN", "").strip()
BASES = [
    "https://api.velocidrone.com",
    "https://www.velocidrone.com/api",
    "https://www.velocidrone.com/apiv2",
    "https://www.velocidrone.com/api/v1",
]
CANDIDATE_PATHS = [
    "/leaderboard/{track_id}",
    "/leaderboards/{track_id}",
    "/tracks/{track_id}/leaderboard",
    "/track/{track_id}",
    "/track/{track_id}/leaderboard",
    "/leaderboard/{track_id}/All",
]


def _headers() -> dict:
    h = {"Accept": "application/json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


def probe(track_id: str) -> None:
    """Δοκίμασε όλους τους πιθανούς συνδυασμούς και τύπωσε τι απαντά ο server."""
    if not TOKEN:
        print("! Δεν έχει οριστεί VELOCIDRONE_TOKEN στο .env")
        print("  Πρόσθεσέ το και ξανατρέξε.")
        return
    print(f"Token: {TOKEN[:12]}... (κρυμμένο)")
    print(f"Track ID: {track_id}\n")
    for base in BASES:
        for path_tpl in CANDIDATE_PATHS:
            url = base + path_tpl.format(track_id=track_id)
            try:
                r = requests.get(url, headers=_headers(), timeout=REQUEST_TIMEOUT)
            except requests.RequestException as e:
                print(f"✗ {url}\n    σφάλμα: {e}")
                continue
            ct = r.headers.get("Content-Type", "")
            print(f"{'✓' if r.status_code == 200 else '·'} [{r.status_code}] {url} ({ct})")
            if r.status_code == 200:
                print("    ", r.text[:300].replace("\n", " "))
    print("\nΣτείλε μου ΟΛΟ αυτό το output - από εκεί γράφω το πραγματικό client.")


def fetch_track(track_id: str) -> list:
    """Θα υλοποιηθεί μόλις κλειδώσουμε endpoint από το probe."""
    raise NotImplementedError(
        "Το endpoint δεν έχει ακόμα επιβεβαιωθεί. Τρέξε πρώτα: "
        "python3 velocidrone_api.py --probe <TRACK_ID>"
    )


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--probe":
        probe(sys.argv[2])
    else:
        print(__doc__)
