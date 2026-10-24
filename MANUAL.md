# 🏁 FPV BOT — Εγχειρίδιο Λειτουργίας

> Ο πλήρης χάρτης του συστήματος. Στόχος: να λειτουργεί οποιοσδήποτε
> χωρίς external βοήθεια. Συνοδευτικό: `TASKS.md` (tasks του NAS),
> `IDEAS.md` (roadmap ιδεών).

---

## 1. Αρχιτεκτονική σε 30 δευτερόλεπτα

```
Velocidrone API ──► NAS (bot, κάθε 5') ──► Discord (ανακοινώσεις)
                        │
                        ├─► site_data.json ──► GitHub ──► Ιστοσελίδα
                        └─► state files (state/standings/duels/quad_names...)
```

- **Repo GitHub** = μοναδική πηγή κώδικα. Το NAS κάνει PULL (δεν επεξεργάζεται κώδικα)
- **NAS** = εκτελεί τα tasks, κρατά τα δεδομένα (state files — ΟΧΙ στο repo)
- **Bot** = push-only (στέλνει στο Discord, δεν διαβάζει)

---

## 2. Η εβδομαδιαία ροή (το «Σαββατιάτικο ριτουάλ»)

| Πότε | Τι | Πώς |
|---|---|---|
| Πριν το Σάββατο | Νέα πίστα ανεβασμένη στο Velocidrone + track_id στην κατοχή σου | Fiddler (βήματα: §5.1) ή από URL του website |
| Σάββατο **18:06** | Η εβδομάδα κλείνει ΑΥΤΟΜΑΤΑ (πόντοι + POTW + embeds) | Το task `FPV-StopWeek` |
| Σάββατο 18:06–βράδυ | Ξεκινάς νέα εβδομάδα | SSH ή task `FPV-Week`: `python3 admin.py week "ΟΝΟΜΑ" --track-id XXXXX` |
| Κυρ/Τρι/Πεμ 21:55 | Recap ποστάρει αυτόματα | Task `FPV-Recap` |
| Κάθε μέρα 03:00 | Backup δεδομένων | Task `FPV-Backup` |
| Κάθε μέρα 04:00 | Pull κώδικα + selftest | Task `FPV-bot update` |

⚠️ **Αν το Σάββατο δεν βάλεις νέα πίστα:** το σύστημα παραμένει παγωμένο — δεν χάνεται τίποτα. Όποτε είσαι έτοιμος, τρέχεις το `FPV-Week`.

---

## 3. Εντολές ανάγκης (SSH cheatsheet)

```bash
cd /volume1/velocidrone-bot        # πάντα από εδώ

# Έλεγχοι
python3 health_check.py            # υγεία συστήματος (τρέχει και από WatchDog)
python3 selftest.py                # πλήρες τεστ (8 ελεγχοι) - μετά από κάθε update!

# Εβδομάδα
python3 admin.py week "Ονομα" --track-id XXXXX   # νέα εβδομάδα (κλείνει την παλιά)
python3 admin.py week-stop                        # κλείσιμο χωρίς νέα πίστα
python3 admin.py week-fix "Ονομα" --track-id XX   # διόρθωση πίστας (νέο id, καθαρός πίνακας)

# Duels
python3 admin.py duel "A" "B" "Πιστα" --days N    # δημιουργία (ανακοινώνει με tags)
python3 admin.py duel-list                        # ενεργά duels
python3 admin.py duel-preview                     # κόντρες υπό παρακολούθηση
python3 admin.py duel-cancel "A" "B"              # ακύρωση

# Πίνακες/βαθμοί
python3 admin.py standings          # βαθμολογία σεζόν στο Discord
python3 admin.py quad scan          # model_ids που πετούν (για χάρτη quads)
python3 admin.py quad               # προβολή χάρτη quad names
python3 admin.py model list         # model_id -> κλάση

# Whitelist
python3 admin.py whitelist          # λίστα μελών
python3 admin.py whitelist add Όνομα1 Όνομα2     # προσθήκη (ID το βάζεις με το χέρι στο CSV)

# GIF / μηνύματα
python3 admin.py test-gif          # τεστ GIF (admin κανάλι)
python3 admin.py msg-stats          # στατιστικά χρήσης μηνυμάτων

# Δεδομένα
python3 backup.py                  # άμεσο backup
tar -xzf backups/ΗΜΕΡΟΜΗΝΙΑ.tar.gz  # επαναφορά (μέσα από τον φάκελο του bot)
tail -100 bot.log                  # πρόσφατα logs
grep "σφάλμα" bot.log | tail -5    # μόνο σφάλματα
```

---

## 4. How-to: Συχνές εργασίες

### 4.1 Νέα πίστα — πώς παίρνω το track_id (Fiddler)

1. Ανοίγεις Fiddler (φίλτρο: `velocidrone`)
2. Στο παιχνίδι: άνοιξε το leaderboard της πίστας (μία φορά)
3. Δεξί κλικ στο request `velocidrone.co.uk` → Save → **Response Body**
4. Στέλνεις το αρχείο σε κάποιον με πρόσβαση στο decryption (ή κρατάς το αρχείο)
5. Από το αποκρυπτογραφημένο JSON παίρνεις `id` και `track_name`

Το id είναι επίσης ορατό στο URL του leaderboard στο website αν η πίστα εμφανίζεται εκεί.

### 4.2 Διόρθωση πίστας (λάθος layout mid-week)

```bash
python3 admin.py week-fix "ΙΔΙΟ_ΟΝΟΜΑ" --track-id ΝΕΟ_ID
```
Κάνει backup, καθαρίζει τους παλιούς χρόνους, ενημερώνει id. Τα πάντα ξεκινούν από 0.

### 4.3 Δημιουργία κόντρας (duel)

```bash
python3 admin.py duel "ΠιλότοςΑ" "ΠιλότοςΒ" "ΟνομαΠιστας" --days 1
```
- Οι πιλότοι πρέπει να είναι στη whitelist **με Discord ID** για να πάρουν tag
- Το `--days 1` σημαίνει: λήξη αύριο την ίδια ώρα. Η κρίση γίνεται αυτόματα στην πρώτη σάρωση μετά τη λήξη
- ⚠️ Η λήξη να είναι **πριν το Σάββατο 18:05** αλλιώς το duel δεν θα κριθεί ποτέ (ο scanner παγώνει στις 18:06)

### 4.4 Προσθήκη μέλους στη whitelist

1. `python3 admin.py whitelist add "ΟνομαVelocidrone"`
2. Ανοίγεις `whitelist.csv` με **Notepad** (ΟΧΙ Excel!) και βάζεις το Discord ID στην 4η στήλη:
   ```csv
   ΟνομαVelocidrone,,,123456789012345678
   ```
   (το ID παίρνεις από Discord: Developer Mode → δεξί κλικ στο μέλος → Copy User ID)
3. Έλεγχος: `python3 -c "from whitelist import mention_map; print(mention_map())"`

### 4.5 Νέα GIF / νέα μηνύματα

- GIF: links σελίδων `giphy.com/gifs/...` στις λίστες `GIF_NEW_TOP` / `GIF_PERSONAL` / `GIF_CROWN` στο `messages.py`
- Μηνύματα: templates στις λίστες `NEW_TOP` / `PERSONAL` / `TEASER` κλπ (μορφή: `"κείμενο με {pilot} {time:.3f} {track}"`)
- Μετά την αλλαγή: push → `FPV-bot update`
- Έλεγχος τι παίζει πολύ: `python3 admin.py msg-stats`

### 4.6 Ανακοίνωση στο Discord (shout) με tags

```bash
python3 -c "from discord_notify import send_discord_message; from whitelist import mention_map; mm=mention_map(); send_discord_message('ΤΟ ΚΕΙΜΕΝΟ', mentions=list(mm.values()))"
```

---

## 5. Αντιμετώπιση προβλημάτων

### Το bot σταμάτησε να ανακοινώνει
1. `python3 health_check.py` — τι δείχνει;
2. `tail -50 bot.log` — σφάλματα;
3. Συνηθισμένο: `grep "σφάλμα στα extras" bot.log | tail -3`

### Κάτι «κόλλησε» (π.χ. λάθος id πίστας)
```bash
python3 admin.py week-fix "Ονομα" --track-id ΣΩΣΤΟ_ID
```

### Corrupted αρχείο δεδομένων
Το bot κάνει αυτόματα recovery (backup με κατάληξη `.corrupt`). Αν χρειαστεί:
```bash
tar -xzf backups/ΤΕΛΕΥΤΑΙΟ.tar.gz   # και ξανατρέχεις
```

### Θέλω να γυρίσω πίσω σε παλιά κατάσταση
```bash
ls backups/                          # δες τι υπάρχει
tar -xzf backups/ΗΜΕΡΟΜΗΝΙΑ.tar.gz   # επαναφορά (ΠΡΟΣΟΧΗ: σκέπασε τρέχοντα!)
```

---

## 6. Χρυσοί κανόνες (που κοστίζουν αν τους σπάσεις)

1. **Ποτέ χειροκίνητη αλλαγή αρχείων στο NAS** — μόνο `whitelist.csv` (και με Notepad). Όλα τα υπόλοιπα μέσω **repo → pull**
2. **Push πάντα ΟΛΟΚΛΗΡΟ το σύνολο αρχείων** (ή έστω προσοχή σε dependencies — αν αλλάξει η μία συνάρτηση, όσοι την καλούν μαζί). Τα μεμονωμένα κομμάτια προκαλούν mismatches
3. Μετά από κάθε update: **`python3 selftest.py`** (ή δες το αποτέλεσμά του στο log από το task)
4. Η εντολή `week` με **ίδιο όνομα** δεν ξαναδίνει πόντους (ασφαλές). Με **--force-award ΔΙΠΛΟΙ πόντοι** — μόνο αν ξέρεις γιατί
5. Duels: η λήξη πριν το Σάββατο 18:05

---

## 7. Πού είναι τι (χάρτης αρχείων)

| Αρχείο | Τι κρατάει | Στο repo; |
|---|---|---|
| `state.json` | χρόνοι/ρεκόρ/καλωσορίσματα/teaser cooldown | ❌ (backup κάθε βράδυ) |
| `standings.json` | βαθμοί σεζόν + ιστορικό | ❌ |
| `duels.json` / `duel_suggestions.json` | κόντρες | ❌ |
| `quad_names.json` | χάρτης 102 quads (id→όνομα) | ❌ |
| `whitelist.csv` | μέλη + Discord IDs | ❌ (μόνο χειροκίνητο) |
| `model_classes.json` | model_id→κλάση | ❌ |
| `backups/` | νυχτερινά tar.gz (7 ημερών) | ❌ |
| Ο κώδικας (.py) | όλο το σύστημα | ✅ |
| `TASKS.md` / `MANUAL.md` / `IDEAS.md` | οδηγοί | ✅ |

---

*Τελευταία ενημέρωση: Οκτώβριος 2025 — κράτα αυτό το αρχείο ζωντανό όποτε αλλάζει κάτι!*
