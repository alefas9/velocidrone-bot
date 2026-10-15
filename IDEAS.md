# FPV Bot — Ιδέες & Roadmap (IDEAS.md)

Πλήρης κατάλογος features: υλοποιημένα, backlog και φρέσκες ιδέες.
Ενημέρωσε το status όταν υλοποιείς κάτι.

---

## ✅ Υλοποιημένα

| Feature | Περιγραφή |
|---|---|
| Αυτόματο leaderboard | API mode, σάρωση κάθε 5' |
| Ανακοινώσεις ρεκόρ + GIF | Auto από Giphy + 11 curated DRL GIFs |
| 👑 Κλοπή κορυφής | Δραματικό μήνυμα όταν ο #2 περνάει τον #1 |
| Teasers | "Η ένταση κόβεται με μαχαίρι" για κλειστές μάχες |
| Duel suggestions | Αυτόματες προτάσεις + @tags |
| Manual duels | Με expiry, ακύρωση, GIF |
| Points / βαθμολογία σεζόν | F1-style, idempotent, --force-award |
| 🌟 Πιλότος της εβδομάδας | Μεγαλύτερη βελτίωση vs προηγούμενη εβδομάδα |
| 🆕 Καλωσόρισμα νέου πιλότου | Μία φορά, με tag |
| Week management | week / week-stop / week-fix |
| Quads | Πλήρης κατάλογος 102 μοντέλων (settings.db) |
| Whitelist + Discord IDs | Mentions παντού |
| Health check / Watchdog | Ωριαίος έλεγχος + alert |
| Nightly backup | 03:00, retention 7 ημερών |
| Site data export | current_leaderboard + quads + history + classes |
| 🧪 Selftest | 8 αυτόματοι έλεγχοι μετά από κάθε update |

---

## 📋 Backlog — κλασικές ιδέες

| # | Feature | Effort | Impact | Status |
|---|---|---|---|---|
| B1 | ⏰ Last Call (24h πριν κλείσει η εβδομάδα) | Μικρό | Υψηλό | |
| B2 | 🗳️ Predictions (ψηφοφορία νικητή) | Μεσαίο ⚠️ | Υψηλό | ⚠️ χρειάζεται real bot (reactions) |
| B3 | 📈 Γράφημα βαθμών σεζόν (εικόνα στο recap) | Μεσαίο | Υψηλό | |
| B4 | 🏅 Τελετή λήξης σεζόν (βραβεία) | Μικρό | Υψηλό | |
| B5 | 🎯 Milestones (έσπασε το 80s!) | Μικρό | Μεσαίο | |
| B6 | 📊 Excel export | Μικρό | Μεσαίο | |
| B7 | 📉 Site: καμπύλη προόδου ανά πιλότο | Μεσαίο | Μεσαίο | (συνομιλία site) |
| B8 | ⚔️ H2H ιστορικό πιλότων | Μικρό | Μεσαίο | |
| B9 | 🗺️ Site: heatmap ωρών δραστηριότητας | Μεσαίο | Χαμηλό | |

---

## 🚀 Φρέσκο (out-of-the-box, αυτόματα/webhook-friendly)

> Σημείωμα: το bot είναι push-only (webhooks). Όλες οι παρακάτω
> λειτουργούν χωρίς καμία ενέργεια/ψήφο από τους πιλότους.

| # | Feature | Περιγραφή | Effort | Impact |
|---|---|---|---|---|
| F1 | 🔥 Streaks | Συνεχόμενες μέρες πτήσης — ανακοινώσεις στα 3/5/7/10 | Μικρό | Υψηλό |
| F2 | 🎯 Auto-Quests | "Βελτίωσε 3x αυτή την εβδομάδα" — auto-tracked + completion | Μεσαίο | Υψηλό |
| F3 | 👑 Μέρες στον θρόνο | Πίνακας ημερών ως #1 ανά πιλότο (recap/site) | Μικρό | Μεσαίο |
| F4 | ⚔️ Auto-Nemesis | Αυτόματο ζευγάρωμα rivals κάθε εβδομάδα, mini-ντέρμπι | Μεσαίο | Μεσαίο |
| F5 | 🎰 Hot Lap Bingo | Σαββατιάτικη έκπληξη challenge με αυτόματο νικητή | Μεσαίο | Μεσαίο |
| F6 | 📖 Auto-ιστορία εβδομάδας | Narrative από stats στην αρχή του recap | Μικρό | Μεσαίο |

---

## Προτερότητα (πρόταση)

1. **F1 + F2 + F3** — η "χρυσή τριάδα": κάθε μέρα πτήση (streak) + στόχος (quest) + κυνήγι κορυφής (throne)
2. **B1 + B4** — εύκολα, άμεσο αποτέλεσμα
3. Τα υπόλοιπα όπως προκύψουν
