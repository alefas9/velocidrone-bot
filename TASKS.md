# FPV Bot — Task Scheduler (NAS)

Ολοκληρωμένος οδηγός όλων των tasks του DSM Task Scheduler.
Αν χρειαστεί να ξαναστηθούν (νέο NAS / reset): Create → Scheduled Task →
User-defined script, user **root**.

> ⚠️ Το DSM δεν έχει "export all" για tasks — αυτό το αρχείο ΕΙΝΑΙ το backup.
> Ενημέρωσέ το κάθε φορά που αλλάζεις task!

---

## Αυτόματα tasks

### 1. FPV-bot Scan — κάθε 5 λεπτά
```
cd /volume1/velocidrone-bot && python3 update_leaderboard.py --once --source auto >> bot.log 2>&1
```

### 2. FPV-bot update — καθημερινά 04:00
```
cd /volume1/velocidrone-bot
git pull --rebase --autostash >> bot.log 2>&1
python3 -m pip install -q -r requirements.txt >> bot.log 2>&1
```

### 3. FPV-Export — κάθε 5 λεπτά (site_data -> repo για το site)
```
cd /volume1/velocidrone-bot
git pull --rebase --autostash -q >>/dev/null 2>&1
python3 export_site_data.py
git add site_data.json
git diff --cached --quiet || git commit -q -m "data update"
git push -q
```

### 4. WatchDog — κάθε ώρα
```
cd /volume1/velocidrone-bot
python3 health_check.py >> bot.log 2>&1
if [ $? -ne 0 ]; then
  python3 -c "from discord_notify import send_discord_admin_message; send_discord_admin_message('🚨 Πρόβλημα στο FPV bot! Έλεγξε το bot.log - κατι θελει φτιξιμο.')"
fi
```

### 5. FPV-Recap — Κυριακή/Τρίτη/Πέμπτη 21:55
```
cd /volume1/velocidrone-bot && python3 post_recap.py >> bot.log 2>&1
```

### 6. FPV-Backup — καθημερινά 03:00
```
cd /volume1/velocidrone-bot && python3 backup.py >> bot.log 2>&1
```

---

## Manual tasks (τρέχουν μόνο με Run — πριν το Run αλλάζεις ονόματα/ids)

### 7. FPV-Week — αλλαγή εβδομάδας
```
cd /volume1/velocidrone-bot && python3 admin.py week "ΟΝΟΜΑ_ΠΙΣΤΑΣ" --track-id XXXXX >> bot.log 2>&1
```
(κλείνει αυτόματα την προηγούμενη εβδομάδα με πόντους)

### 8. FPV-StopWeek — κλείσιμο εβδομάδας χωρίς νέα πίστα
```
cd /volume1/velocidrone-bot && python3 admin.py week-stop >> bot.log 2>&1
```

### 9. FPV-WeekFix — επανα-ανέβασμα ίδιας πίστας (διόρθωση layout)
```
cd /volume1/velocidrone-bot && python3 admin.py week-fix "ΟΝΟΜΑ_ΠΙΣΤΑΣ" --track-id XXXXX >> bot.log 2>&1
```

### 10. FPV-Duels — δημιουργία duel
```
cd /volume1/velocidrone-bot && python3 admin.py duel "ΠΙΛΟΤΟΣ_Α" "ΠΙΛΟΤΟΣ_Β" "ΠΙΣΤΑ" --days 3 >> bot.log 2>&1
```

### 11. FPV-Cancel Duels — ακύρωση duel
```
cd /volume1/velocidrone-bot && python3 admin.py duel-cancel "ΠΙΛΟΤΟΣ_Α" "ΠΙΛΟΤΟΣ_Β" >> bot.log 2>&1
```

---

## ΔΙΑΓΡΑΜΜΕΝΑ (μην ξαναφτιάξεις!)
- ~~FPV-Bot Install~~ — είχε μείνει daily και μόλυνε το state με demo δεδομένα
- ~~FPV-Fix~~ / ~~FPV-Probe~~ — διπλότυπα debug του FPV-Export

## Εντολές ανάγκης (SSH)
```bash
cd /volume1/velocidrone-bot
python3 health_check.py              # έλεγχος υγείας
python3 admin.py week-stop           # κλείσιμο εβδομάδας
python3 admin.py standings           # βαθμολογία σεζόν -> Discord
python3 admin.py test-gif            # τεστ GIF (admin κανάλι)
python3 backup.py                    # άμεσο backup
tar -xzf backups/ΗΜΕΡΟΜΗΝΙΑ.tar.gz   # επαναφορά από backup
```
