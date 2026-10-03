# Velocidrone Leaderboard Bot (Discord)

Bot που διαβάζει leaderboards από το **Velocidrone** και ποστάρει στο **Discord** κανάλι σας:
νέα ρεκόρ σε real-time, proximity teasers, head-to-head duels, θεματικές κατηγορίες tracks
και μηνιαίο recap.

## Πώς δουλεύει (data flow)

```
Velocidrone (in-game) --[Export leaderboard -> CSV]--> tracks/ φάκελος
                                                              |
                            update_leaderboard.py (polling)   v
                                         Discord Webhook  <---+  state.json / duels.json
```

Το Velocidrone έχει **built-in export button** στο leaderboard που παράγει `.csv`
(βλ. VelociDrone manual, ενότητα Leaderboards). Ρίχνετε το CSV στον φάκελο `tracks/`
(όνομα αρχείου = όνομα track) και το bot κάνει τα υπόλοιπα. Όποιος πετύχει βελτίωση
χρόνου, ανακοινώνεται αυτόματα στο Discord — χωρίς scraping, χωρίς login.

> Tip: αφήστε έναν υπεύθυνο της ομάδας να κάνει export τα leaderboards μία φορά την ημέρα,
> ή μετά από κάθε "race night". Για πιο συχνό polling βάλτε το `--loop`.

## Setup (5 λεπτά)

```bash
# 1. Εξαρτήσεις
pip install -r requirements.txt

# 2. Ρυθμίσεις
cp .env.example .env
# άνοιξε το .env και βάλε το Discord webhook URL του καναλιού σου:
#   Channel -> Settings -> Integrations -> Webhooks -> New Webhook -> Copy URL

# 3. Φάκελος για τα CSV exports
mkdir tracks

# 4. Demo (χωρίς Velocidrone - βλέπεις τι θα ποσταριστεί)
python update_leaderboard.py --once --demo

# 5. Πραγματική χρήση - ρίξε CSV exports στο tracks/ και τρέξε:
python update_leaderboard.py --once          # μία σάρωση
python update_leaderboard.py --loop 300      # ή συνεχές polling κάθε 5 λεπτά
```

## Discord posts

- **Νέο ρεκόρ**: embed με το top-10 leaderboard (🥇🥈🥉) αμέσως μόλις ανιχνευθεί βελτίωση
- **Proximity teaser**: ⚡ "ο X χρειάζεται 0.3s για να πάρει το #1" όταν η μάχη είναι κλειστή
- **Duels**: 🏆 αυτόματη ανακοίνωση νικητή όταν λήξει η προθεσμία

## Admin / cron

```bash
python admin.py duel "Nikos" "Maria" "Bando Track" --days 3   # πρόκληση 1-1
python admin.py recap 2026 10                                  # μηνιαίο recap στο Discord
python admin.py category "Bando Track" racing                  # tag track (βλ. παρακάτω)
```

Cron παραδείγματα (crontab -e):
```cron
# Σάρωση κάθε 5 λεπτά
*/5 * * * *  cd /path/to/velocidrone-bot && python update_leaderboard.py --once
# Μηνιαίο recap 1η του μήνα 09:00
0 9 1 * *    cd /path/to/velocidrone-bot && python admin.py recap $(date +\%Y) $(date +\%-m)
```

## Κατηγορίες tracks (θεματικές ημέρες)

Ενημέρωσε το `TRACK_CATEGORIES` στο `track_categories.py` με τα δικά σου tracks
(το όνομα πρέπει να ταιριάζει ΑΚΡΙΒΩΣ με το όνομα του CSV αρχείου).

## Αρχεία

| Αρχείο | Ρόλος |
|---|---|
| `update_leaderboard.py` | Κύριο script (polling + ανακοινώσεις) |
| `velocidrone_source.py` | Parser για τα CSV exports (`--inspect` για debug) |
| `discord_notify.py` | Αποστολή σε Discord webhook |
| `db.py` / `state.json` | Αποθήκευση καλύτερων χρόνων + ιστορικού |
| `leaderboard_format.py` | Μορφοποίηση leaderboard + proximity teaser |
| `duels.py` / `duels.json` | Head-to-head duels |
| `track_categories.py` | Κατηγορίες tracks |
| `monthly_recap.py` | Μηνιαίο recap |
| `admin.py` | CLI εργαλεία |

## Εβδομαδιαία λειτουργία (η ροή σας)

Κάθε εβδομάδα ο admin τρέχει ΜΙΑ εντολή:

```bash
python admin.py week "Ονομα Πιστας" "URL_leaderboard_απο_velocidrone.com"
```

- Το bot ανακοινώνει αυτόματα την πίστα στο Discord (📢 Πίστα εβδομάδας)
- Παρακολουθεί συνεχώς το leaderboard: `python update_leaderboard.py --loop 300 --source web`
- Οι πιλότοι δεν κάνουν ΤΙΠΟΤΑ επιπλέον - αρκεί το in-game setting
  **Options → Main Settings → Auto Leaderboard Upload: Yes** (μία φορά)
- Κάθε νέος χρόνος -> ανακοίνωση στο Discord, **χωρισμένη ανά κλάση**
  (🏁 5 Inch / 🐝 Whoop) με βάση το μοντέλο quad που κατέγραψε ο πιλότος

### Πού βρίσκω το URL της πίστας;

Στο browser: velocidrone.com → Leaderboards → διάλεξε πίστα → αντιγραφή του URL
από τη γραμμή διευθύνσεων. Αυτό είναι όλο - ο admin το χρειάζεται 1 φορά/εβδομάδα.

### Τα μοντέλα της κοινότητάς σου

Ο χάρτης μοντέλων -> κλάση είναι στην κορυφή του `velocidrone_web.py` (CLASS_MAP).
Πρόσθεσε τα μοντέλα που πετάνε οι δικοί σας πιλότοι.

### Πρώτη εγκατάσταση - βήμα-βήμα

```bash
pip install -r requirements.txt
cp .env.example .env        # βάλε το Discord webhook URL
# 1. Ο admin ορίζει πίστα:
python admin.py week "Bando Track" "https://www.velocidrone.com/leaderboard/..."
# 2. Δοκιμή τι βλέπει το bot από το site:
python velocidrone_web.py --probe "https://www.velocidrone.com/leaderboard/..."
# 3. Τρέξιμο:
python update_leaderboard.py --loop 300 --source web
```
