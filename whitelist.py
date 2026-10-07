"""
whitelist.py

Λίστα μελών κοινότητας σε αρχείο CSV (ανοίγει με Excel/Notepad).

Αρχείο: whitelist.csv (δίπλα στα scripts) με μορφή:

    name,discord,class,discord_id
    ZOUP,@zoup,5inch,123456789012345678
    tomahok,,,
    DedalosFPV,@dedalos,,

- Πρώτη γραμμή = κεφαλίδες (name, discord, class - το discord/class προαιρετικά)
- Μία γραμμή ανά πιλότο. Οτιδήποτε μετά την 1η κολώνα (discord/class) είναι
  για δική σας οργάνωση - το bot κοιτά ΜΟΝΟ το name.
- Μπορείς να το επεξεργαστείς με Excel (Save as: CSV UTF-8) ή απευθείας στο NAS.

Αν η λίστα ΔΕΝ είναι άδεια, μόνο τα μέλη εμφανίζονται στο leaderboard
(API / Web / CSV). Αν είναι άδεια -> όλοι ορατοί.

Γρήγορη διαχείριση από admin.py:
  python3 admin.py whitelist add "ZOUP" "tomahok"
  python3 admin.py whitelist remove "SomeName"
  python3 admin.py whitelist list
"""
from __future__ import annotations

import csv
import json
import os

WHITELIST_CSV = os.environ.get("WHITELIST_CSV", "whitelist.csv")
WHITELIST_JSON = os.environ.get("WHITELIST_FILE", "whitelist.json")  # legacy


def _read_csv() -> list:
    """Λίστα dicts {name, discord, class} από το csv (αντέχει BOM, κενές γραμμές)."""
    if not os.path.exists(WHITELIST_CSV):
        return []
    # Η κεφαλίδα αναγνωρίζεται με πολλές λέξει-κλειδιά (ακόμα κι αν τα
    # έχεις μετονομάσει στα ελληνικά / ταξινομήσει λάθος στο Excel).
    HEADER_WORDS = ("name", "pilot", "ονομ", "πίλοτ", "player")
    rows = []
    with open(WHITELIST_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not str(row[0]).strip():
                continue
            first = str(row[0]).strip()
            if first.startswith("#"):
                continue
            if any(w in first.lower() for w in HEADER_WORDS):
                continue  # header (σε οποιαδήποτε γραμμή)
            rows.append({
                "name": first,
                "discord": str(row[1]).strip() if len(row) > 1 else "",
                "class": str(row[2]).strip() if len(row) > 2 else "",
                "discord_id": str(row[3]).strip() if len(row) > 3 else "",
            })
    return rows


def _write_csv(rows: list) -> None:
    with open(WHITELIST_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "discord", "class"])
        for r in rows:
            w.writerow([r["name"], r.get("discord", ""), r.get("class", ""),
                        r.get("discord_id", "")])


def load() -> set:
    """set με lowercase ονόματα."""
    names = {r["name"].lower() for r in _read_csv()}
    # legacy json υποστήριξη (μόνο αν δεν υπάρχει csv)
    if not names and os.path.exists(WHITELIST_JSON):
        try:
            with open(WHITELIST_JSON, encoding="utf-8") as f:
                data = json.load(f)
            names = {str(n).strip().lower() for n in data if str(n).strip()}
        except (json.JSONDecodeError, OSError):
            pass
    return names


def members() -> list:
    return _read_csv()


def mention_map() -> dict:
    """{ονομα_πίλοτου_lower: discord_id} - μόνο για όσους έχουν δηλώσει ID."""
    return {r["name"].lower(): r.get("discord_id", "")
            for r in _read_csv() if r.get("discord_id", "").isdigit()}


def to_mention(name: str, mmap: dict | None = None) -> str:
    """'<@ID>' αν υπάρχει ID, αλλιώς το όνομα ως έχει."""
    mm = mmap if mmap is not None else mention_map()
    mid = mm.get(name.lower())
    return f"<@{mid}>" if mid else name


def add(names: list) -> int:
    rows = _read_csv()
    existing = {r["name"].lower() for r in rows}
    added = 0
    for n in names:
        n = n.strip()
        if n and n.lower() not in existing:
            rows.append({"name": n, "discord": "", "class": ""})
            existing.add(n.lower())
            added += 1
    if added:
        _write_csv(rows)
    return added


def remove(names: list) -> int:
    rows = _read_csv()
    targets = {n.strip().lower() for n in names}
    before = len(rows)
    rows = [r for r in rows if r["name"].lower() not in targets]
    removed = before - len(rows)
    if removed:
        _write_csv(rows)
    return removed


def active() -> bool:
    return bool(load())


def filter_entries(entries: list) -> list:
    wl = load()
    if not wl:
        return entries
    return [e for e in entries if str(e.get("pilot", "")).strip().lower() in wl]
