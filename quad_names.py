"""
quad_names.py

Χάρτης model_id -> εμφανίσιμο όνομα quad.

ΓΙΑΤΙ: το Velocidrone API επιστρέφει μόνο αριθμητικό model_id (π.χ. 123),
όχι όνομα. Το site (και το Discord) θέλουν όμως "Five33 Switchback".
Ο admin ορίζει τα ονόματα ΜΙΑ ΦΟΡΑ:

    python3 admin.py quad              # προβολή χάρτη
    python3 admin.py quad 123 "Five33 Switchback"

Το αρχείο quad_names.json δημιουργείται αυτόματα στον φάκελο του bot.
"""

import json
import os

QUAD_NAMES_FILE = "quad_names.json"


def load() -> dict:
    """{model_id_str: name} - {} αν δεν υπάρχει/corrupted."""
    if not os.path.exists(QUAD_NAMES_FILE):
        return {}
    try:
        with open(QUAD_NAMES_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def save(mapping: dict) -> None:
    # atomic write: ποτέ half-written file
    tmp = QUAD_NAMES_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    os.replace(tmp, QUAD_NAMES_FILE)


def set_name(model_id, name: str) -> None:
    mapping = load()
    mapping[str(model_id)] = name
    save(mapping)


def get_name(model_id) -> str:
    """Όνομα quad για model_id ή "" αν δεν είναι χαρτογραφημένο."""
    return load().get(str(model_id), "")
