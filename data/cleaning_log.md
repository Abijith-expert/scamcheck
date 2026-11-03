# Cleaning log

| Step | Count |
|---|---|
| 1. Rows at start | 5574 |
| 2. Rows changed by HTML fix (&lt; &gt; &amp; ...) | 309 |
| 3. Rows changed by stripping extra spaces | 424 |
| 4. Exact duplicate messages removed | 414 |
| Rows after cleaning | 5160 |
| Train rows (80%) | 4128 |
| Test rows (20%) | 1032 |

Duplicate removal was moved after the HTML fix and space stripping, because cleaning creates new duplicates (6 messages were in both train and test before).

## Class balance

- Before cleaning: ham 4827 (86.6%), spam 747 (13.4%)
- After cleaning: ham 4518 (87.6%), spam 642 (12.4%)
- Train: ham 3614 (87.5%), spam 514 (12.5%)
- Test: ham 904 (87.6%), spam 128 (12.4%)

## Rule not in the file

**Source:** Cybermalveillance.gouv.fr (the French government's cybersecurity assistance platform), leaflet "L'hameçonnage":
https://www.cybermalveillance.gouv.fr/medias/2026/02/260129_FicheReflexe_Hameconnage.pdf
Consulted on 2 November 2026.

**What it says:** "aucune administration ou société commerciale sérieuse ne vous demandera vos données bancaires ou vos mots de passe par message électronique ou par téléphone."
(No serious administration or company will ever ask for your bank details or passwords by message or by phone.)

**The rule I apply:** a message that asks the reader for bank details, a password, or a payment through a link is treated as a scam, whoever claims to send it (bank, Ameli, CAF, Colissimo...).

**Why it's needed:** the dataset only says spam or ham, never why. This rule gives a reason that comes from an official source, not from the data. It is used in tools/tactics.py and check_sms to flag these requests, and it is what the explanation shown to the user is based on.
