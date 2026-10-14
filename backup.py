"""
backup.py

Νυχτερινό backup των state αρχείων σε backups/ με retention KEEP_DAYS ημερών.

Χρήση (task "FPV-Backup" στις 03:00 ή χειροκίνητα):
    python3 backup.py

- Συμπιέζει τα δεδομένα της σεζόν σε backups/ΕΕΕΕ-ΜΜ-ΗΗ.tar.gz
- Κρατάει τις πιο πρόσφατες KEEP_DAYS ημέρες (σβήνει παλιότερα)
- Σε αποτυχία στέλνει alert στο admin κανάλι
- Επαναφορά σε κρίση:
      cd /volume1/velocidrone-bot
      tar -xzf backups/ΕΕΕΕ-ΜΜ-ΗΗ.tar.gz
"""

import datetime
import os
import tarfile

# Τα αρχεία που κρατάνε όλη τη σεζόν (runtime data - ΔΕΝ είναι στο git)
FILES = [
    "state.json",
    "standings.json",
    "duels.json",
    "duel_suggestions.json",
    "quad_names.json",
    "model_classes.json",
    "weekly_track.json",
    "whitelist.csv",
    "TASKS.md",          # οδηγός tasks (κύριο αντίγραφο στο git repo)
]
BACKUP_DIR = "backups"
KEEP_DAYS = 7


def run_backup() -> tuple:
    """Δημιουργεί το tar.gz και εφαρμόζει retention.

    Επιστρέφει (path, missing) - missing = αρχεία που δεν υπήρχαν
    (π.χ. δεν έχει γίνει ακόμα κάποιο duel -> duels.json λείπει).
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(BACKUP_DIR, f"{stamp}.tar.gz")
    present = [f for f in FILES if os.path.exists(f)]
    missing = [f for f in FILES if not os.path.exists(f)]
    if not present:
        raise RuntimeError(f"κανένα αρχείο δεν βρέθηκε (cwd={os.getcwd()})")

    with tarfile.open(path, "w:gz") as tar:
        for f in present:
            tar.add(f)

    # retention: κράτα μόνο τα πιο πρόσφατα KEEP_DAYS
    backups = sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith(".tar.gz"))
    for old in backups[:-KEEP_DAYS]:
        os.remove(os.path.join(BACKUP_DIR, old))
    return path, missing


def main() -> None:
    try:
        path, missing = run_backup()
        size_kb = os.path.getsize(path) // 1024
        msg = f"💾 Backup OK: {path} ({size_kb}KB, {KEEP_DAYS} ημέρες retention)"
        if missing:
            msg += f" | έλειπαν: {', '.join(missing)}"
        print(msg)
    except Exception as e:
        print(f"❌ Backup απέτυχε: {e}")
        try:
            from discord_notify import send_discord_admin_message
            send_discord_admin_message(f"🚨 FPV Backup απέτυχε: {e}")
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
