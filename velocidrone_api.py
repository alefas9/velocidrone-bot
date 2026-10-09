"""
velocidrone_api.py

ΕΠΙΣΗΜΟ Velocidrone API client - ΠΛΗΡΩΣ ΑΥΤΟΜΑΤΟ για ΟΛΕΣ τις πίστες
(official + community/custom), χωρίς CSV, χωρίς webhook-scraping.

Πηγή ανακάλυψης endpoints/κρυπτογράφησης: opensource project FPVBattle
(github.com/UaVelocidroneBattle/FPVBattle - Veloci.Logic/API/Velocidrone.cs,
Services/Encryption.cs) - AES-128-ECB/PKCS7 με κλειδί "BatCaveGGevaCtaB".

Δύο τρόποι λειτουργίας:
1) SIM MODE (χωρίς token) - αναπαράγει ακριβώς τι στέλνει το sim:
     POST https://velocidrone.co.uk/api/leaderboard/getLeaderBoard
     body: post_data=<urlencode(base64(AES_ECB(params)))>
     -> η απάντηση είναι AES-κρυπτογραφημένη, την αποκρυπτογραφούμε
2) TOKEN MODE (αν ποτέ πάρεις bearer token):
     POST https://velocidrone.co.uk/api/leaderboard
     Authorization: Bearer <token>, post_data=<urlencode(plain params)>
     -> απάντηση καθαρό JSON

Παράμετροι leaderboard: track_id, sim_version, offset, count, race_mode
(race_mode=6 όπως χρησιμοποιεί το FPVBattle - single class 3 laps)

Χρήση:
  python3 velocidrone_api.py --probe 2167        # γρήγορη δοκιμή με track id
  ή από κώδικα: entries = fetch_leaderboard(2167)
"""

import base64
import os
import json
import sys
import urllib.parse

import requests

try:
    from Crypto.Cipher import AES
except ImportError:
    print("Χρειάζεται: python3 -m pip install pycryptodome")
    raise

from config import REQUEST_TIMEOUT

BASE = "https://velocidrone.co.uk"
KEY = b"BatCaveGGevaCtaB"          # AES-128 (16 bytes) - από FPVBattle Encryption.cs
# optional bearer token (token mode) - ορίζεται στο .env ως VELOCIDRONE_TOKEN
TOKEN = os.environ.get("VELOCIDRONE_TOKEN", "").strip()

BLOCK = 16

# model_id -> κλάση. Επιβεβαιωμένα από σταύρωση CSV+API:
#   55=TBS Spec (5"), 59=Five33 Switchback (5"), 108=LightSwitch (5"),
#   66=Twig XL 3 (3" - αν θες μόνο 2 κλάσεις βάλ' το whoop)
# Επιπλέον mappings στο model_classes.json (δίπλα στα scripts - το γεμίζεις
# χειροκίνητα ή με: python3 admin.py model 123 whoop)
MODEL_ID_CLASSES = {
    55: "5inch",    # TBS Spec
    59: "5inch",    # Five33 Switchback
    108: "5inch",   # LightSwitch
    66: "5inch",    # Twig XL 3 (όλα 5inch προς το παρόν)
}

# Κλάση για ΟΛΑ τα μη-χαρτογραφημένα model_ids (μόνο 2 κλάσεις στο σύστημα!)
DEFAULT_CLASS = os.environ.get("DEFAULT_CLASS", "5inch")

MODEL_CLASSES_FILE = os.environ.get("MODEL_CLASSES_FILE", "model_classes.json")


def load_model_classes() -> dict:
    """Βασικός χάρτης + ό,τι έχεις ορίσει στο model_classes.json."""
    result = dict(MODEL_ID_CLASSES)
    if os.path.exists(MODEL_CLASSES_FILE):
        try:
            with open(MODEL_CLASSES_FILE, encoding="utf-8") as f:
                extra = json.load(f)
            for k, v in extra.items():
                result[int(k)] = str(v)
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    return result


def set_model_class(model_id: int, cls: str) -> None:
    """Αποθήκευσε mapping (γράφει στο model_classes.json)."""
    extra = {}
    if os.path.exists(MODEL_CLASSES_FILE):
        try:
            with open(MODEL_CLASSES_FILE, encoding="utf-8") as f:
                extra = json.load(f)
        except (json.JSONDecodeError, OSError):
            extra = {}
    extra[str(model_id)] = cls
    with open(MODEL_CLASSES_FILE, "w", encoding="utf-8") as f:
        json.dump(extra, f, ensure_ascii=False, indent=2)


def _pkcs7_pad(data: bytes) -> bytes:
    pad = BLOCK - (len(data) % BLOCK)
    return data + bytes([pad]) * pad


def _pkcs7_unpad(data: bytes) -> bytes:
    pad = data[-1]
    if pad < 1 or pad > BLOCK:
        raise ValueError("invalid PKCS7 padding")
    return data[:-pad]


def encrypt(plain: str) -> str:
    """AES-128-ECB + PKCS7 -> base64 (ίδιο με το Encryption.Encrypt του FPVBattle)."""
    cipher = AES.new(KEY, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(_pkcs7_pad(plain.encode()))).decode()


def decrypt(blob_b64: str) -> str:
    cipher = AES.new(KEY, AES.MODE_ECB)
    raw = base64.b64decode(blob_b64)
    return _pkcs7_unpad(cipher.decrypt(raw)).decode(errors="replace")


def build_params(track_id: int, race_mode: int = 6, count: int = 2000,
                 offset: int = 0, sim_version: str = "1.16",
                 protected_track_value: int = 2, model_id: int = 59,
                 quad_class: int = 0) -> str:
    """Ακριβές format από αποκρυπτογράφηση πραγματικού sim request:
    track_id=37845&sim_version=1.16&offset=0&count=15&protected_track_value=2
    &model_id=59&race_mode=6&quad_class=0
    (model_id/quad_class: πιθανό wildcard=59/0 - θα επιβεβαιωθεί στο probe)"""
    return (f"track_id={track_id}&sim_version={sim_version}&offset={offset}"
            f"&count={count}&protected_track_value={protected_track_value}"
            f"&model_id={model_id}&race_mode={race_mode}&quad_class={quad_class}")


def fetch_leaderboard(track_id: int, race_mode: int = 6, **kw) -> list:
    """Επιστρέφει [{pilot, time, ...}] ή ρίχνει exception με το status."""
    params = build_params(track_id, race_mode, **kw)
    headers = {"User-Agent": "UnityPlayer/2021.3.45f2 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
               "X-Unity-Version": "2021.3.45f2"}

    if TOKEN:
        # TOKEN MODE: καθαρό JSON
        headers["Authorization"] = f"Bearer {TOKEN}"
        url = f"{BASE}/api/leaderboard"
        body = "post_data=" + urllib.parse.quote_plus(params)
    else:
        # SIM MODE: κρυπτογραφημένο (όπως το sim)
        url = f"{BASE}/api/leaderboard/getLeaderBoard"
        body = "post_data=" + urllib.parse.quote_plus(encrypt(params))
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    r = requests.post(url, data=body.encode(), headers=headers,
                      timeout=REQUEST_TIMEOUT)

    # Απάντηση: plaintext JSON ή base64-AES
    text = r.text.strip()
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code}: {text[:300]}")
    if text.startswith("{"):
        data = json.loads(text)
    else:
        try:
            data = json.loads(decrypt(text))
        except Exception:
            data = json.loads(text)   # fallback

    # Πραγματικό format απάντησης (αποκρυπτογραφημένο από live capture):
    # {"success":true,"tracktimes":[{"lap_time":"30.804","playername":"OutsetFPV",
    #   "model_id":123,"country":"US","sim_version":"1.16","device_type":0,"user_id":...}]}
    times = data.get("tracktimes") or []
    out = []
    for e in times:
        try:
            out.append({
                "pilot": e["playername"],
                "time": float(e["lap_time"]),
                "model_id": e.get("model_id"),
                "country": e.get("country"),
                "class": load_model_classes().get(e.get("model_id")) or DEFAULT_CLASS,
            })
        except (KeyError, ValueError, TypeError):
            continue
    out.sort(key=lambda x: x["time"])
    return out


def probe(track_id: int) -> None:
    print(f"Probe track_id={track_id} ({'token mode' if TOKEN else 'sim mode'})")
    try:
        entries = fetch_leaderboard(track_id)
    except Exception as e:
        print(f"✗ {e}")
        return
    print(f"✓ {len(entries)} εγγραφές (ολες)")
    for e in entries:
        print(f"  {e['pilot']:<18} {e['time']:>9.3f}s  model_id={e.get('model_id')} -> {e['class']}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--probe":
        probe(int(sys.argv[2]))
    else:
        # self-test κρυπτογράφησης (round-trip)
        p = build_params(2167)
        assert decrypt(encrypt(p)) == p
        print("crypto round-trip OK ✓")
        print("Χρήση: python3 velocidrone_api.py --probe <TRACK_ID>")
