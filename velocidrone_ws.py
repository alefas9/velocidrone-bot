"""
velocidrone_ws.py

LIVE WebSocket listener - το sim μιλάει απευθείας στο bot!

ΠΡΟΑΠΑΙΤΟΥΜΕΝΑ:
1. Στο PC που τρέχει το Velocidrone: Options → Main Settings
   → "Websocket Communication" = Yes
2. Στο .env: VELO_WS_IP = το IP του PC (π.χ. 192.168.1.50)
3. pip: python3 -m pip install websocket-client

ΠΩΣ ΔΟΥΛΕΥΕΙ:
- Συνδέεται στο ws://IP:60003/velocidrone (με auto-reconnect)
- Κάθε μήνυμα JSON: racestatus / racedata / pilotlist / FinishGate
- Στο "race finished": στέλνει στο Discord τελική κατάταξη με
  🥇🥈🥉 + proximity teaser (ποιος κέρδισε με διαφορά < 0.5s)
- Τρέχει σαν long-lived process (δες launcher στο README)

Μορφή racedata (από το επίσημο RotorHazard plugin):
  {"racedata": {"PilotName": {"uid": "123", "lap": 2, "time": 77.42,
                               "gate": 3, "finished": "false"}}}
"""

import json
import os
import threading
import time

from websocket import WebSocketApp

from discord_notify import send_discord_message, send_discord_embed
from leaderboard_format import proximity_teaser

WS_PORT = 60003
WS_PATH = "/velocidrone"
RECONNECT_DELAY = 10

VELO_WS_IP = os.environ.get("VELO_WS_IP", "").strip()


class RaceTracker:
    """Κρατάει το state του τρέχοντος αγώνα."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.pilots = {}      # name -> {uid, laps: [lap_times], cum: last_cumulative, finished}
        self.started = False

    def handle_status(self, status: dict) -> None:
        action = (status.get("raceAction") or "").lower()
        if action == "start":
            self.reset()
            self.started = True
            from messages import RACE_START, pick
            send_discord_message(pick(RACE_START))
        elif action == "abort":
            self.reset()
            send_discord_message("⛔ Ο αγώνας ματαιώθηκε.")
        elif action == "race finished" and self.started:
            self.announce_results()
            self.reset()

    def handle_data(self, data: dict) -> None:
        if not self.started:
            return
        for name, pd in data.items():
            p = self.pilots.setdefault(name, {"uid": pd.get("uid"), "laps": [],
                                              "cum": 0.0, "finished": False})
            t = float(pd.get("time", 0))
            lap = int(pd.get("lap", 0))
            finished = str(pd.get("finished", "false")).lower() == "true"
            # νέος γύρος -> lap time = διαφορά cumulative
            if lap > len(p["laps"]) + 1 and p["cum"]:
                p["laps"].append(round(t - p["cum"], 3))
            p["cum"] = t
            if finished:
                if not p["finished"] and p["laps"]:
                    pass  # ο τελευταίος γύρος μετράει στο cumulative
                p["finished"] = True

    def results(self) -> list:
        out = []
        for name, p in self.pilots.items():
            if p["cum"] > 0:
                out.append({"pilot": name, "time": p["cum"],
                            "best_lap": min(p["laps"]) if p["laps"] else None,
                            "laps": len(p["laps"]) + 1})
        out.sort(key=lambda e: e["time"])
        return out

    def announce_results(self) -> None:
        res = self.results()
        if not res:
            return
        fields = []
        for i, r in enumerate(res[:10], 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
            extra = f" (best lap {r['best_lap']:.3f}s)" if r["best_lap"] else ""
            fields.append({"name": f"{medal} {r['pilot']}",
                           "value": f"{r['time']:.3f}s{extra}", "inline": True})
        winner = res[0]
        from messages import RACE_FINISH_TITLE, RACE_FINISH_CTA, pick
        import random
        desc = pick(RACE_FINISH_CTA) if random.random() < 0.35 else ""
        send_discord_embed(
            title=pick(RACE_FINISH_TITLE).format(
                winner=winner["pilot"], time=winner["time"]),
            description=desc,
            fields=fields,
        )
        teaser = proximity_teaser([{"pilot": r["pilot"], "time": r["time"]} for r in res])
        if teaser:
            send_discord_message(teaser)


tracker = RaceTracker()


def on_message(ws, raw):
    try:
        msg = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return  # ping/άγνωστο
    if "racestatus" in msg:
        tracker.handle_status(msg["racestatus"])
    elif "racedata" in msg:
        tracker.handle_data(msg["racedata"])
    elif "pilotlist" in msg:
        names = [p.get("name", "?") for p in msg["pilotlist"]]
        send_discord_message(f"👥 Πιλότοι στο room: {', '.join(names)}")


def on_error(ws, error):
    print(f"[ws] σφάλμα: {error}")


def on_close(ws, code, msg):
    print(f"[ws] έκλεισε ({code}): {msg} - ξανασυνδέομαι σε {RECONNECT_DELAY}s")


def on_open(ws):
    print("[ws] συνδέθηκα στο Velocidrone ✓")
    if os.environ.get("WS_ANNOUNCE"):
        from messages import WS_CONNECTED, pick
        send_discord_message(pick(WS_CONNECTED))


def main():
    if not VELO_WS_IP:
        print("! Βάλε VELO_WS_IP στο .env (το IP του PC που τρέχει το Velocidrone)")
        return
    url = f"ws://{VELO_WS_IP}:{WS_PORT}{WS_PATH}"
    print(f"Σύνδεση στο {url} ...")
    while True:
        ws = WebSocketApp(url, on_message=on_message, on_error=on_error,
                          on_close=on_close, on_open=on_open)
        ws.run_forever(ping_interval=0)   # το plugin στέλνει δικά του pings
        time.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    main()
