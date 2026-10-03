"""
db.py

Απλό persistence σε JSON (state.json) - αρκεί για community scale.
Κρατάει:
  - best γνωστό χρόνο ανά (track, pilot)  -> για να ανιχνεύουμε βελτιώσεις
  - records_log                           -> για το μηνιαίο recap
"""

import json
import os
import threading

from config import STATE_FILE

_lock = threading.Lock()


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {"tracks": {}, "records_log": []}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
    # migration: παλιά μορφή {track: {pilot: time}} -> {track: {"": {pilot: time}}}
    for track, pilots in state.get("tracks", {}).items():
        if pilots and not isinstance(next(iter(pilots.values())), dict):
            state["tracks"][track] = {"": pilots}
    return state


def save_state(state: dict) -> None:
    with _lock:
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, STATE_FILE)


def get_best(state: dict, track: str, pilot: str, cls: str = ""):
    return state["tracks"].get(track, {}).get(cls or "", {}).get(pilot)


def set_best(state: dict, track: str, pilot: str, time: float, cls: str = "") -> None:
    state["tracks"].setdefault(track, {}).setdefault(cls or "", {})[pilot] = time


def log_record(state: dict, pilot: str, track: str, time: float, date: str) -> None:
    state["records_log"].append(
        {"pilot": pilot, "track": track, "time": time, "date": date}
    )
