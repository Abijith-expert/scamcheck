"""Clean the raw SMS data, split it 80/20 and write a cleaning log."""
import csv
import html
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

DATA = Path(__file__).parent


def clean(df):
    """Return the cleaned data and a dict with the counts for the log."""
    counts = {"rows_start": len(df)}

    # 2. fix HTML leftovers like &lt; &gt; &amp;
    fixed = df["message"].apply(html.unescape)
    counts["html_rows_changed"] = int((fixed != df["message"]).sum())
    df = df.assign(message=fixed)

    # 3. strip extra spaces (start, end and repeated spaces inside)
    stripped = df["message"].apply(lambda text: " ".join(text.split()))
    counts["space_rows_changed"] = int((stripped != df["message"]).sum())
    df = df.assign(message=stripped)

    # 4. remove exact duplicate messages, AFTER steps 2 and 3 so that
    #    "a &amp; b" and "a  & b" are seen as the same message
    rows_before = len(df)
    df = df.drop_duplicates(subset="message")
    counts["duplicates_removed"] = rows_before - len(df)

    # 5. labels -> spam=1, ham=0
    df = df.assign(label=df["label"].map({"spam": 1, "ham": 0}))

    counts["rows_end"] = len(df)
    return df, counts


def split(df, test_size=0.2):
    """6. stratified train/test split, done only after cleaning."""
    return train_test_split(df, test_size=test_size, stratify=df["label"], random_state=42)


def balance(labels):
    """Text like 'ham 4825 (86.6%), spam 747 (13.4%)'."""
    n = len(labels)
    ham = int((labels == 0).sum())
    spam = int((labels == 1).sum())
    return f"ham {ham} ({ham / n:.1%}), spam {spam} ({spam / n:.1%})"


def write_log(counts, raw, cleaned, train, test):
    raw_labels = raw["label"].map({"spam": 1, "ham": 0})
    log = f"""# Cleaning log

| Step | Count |
|---|---|
| 1. Rows at start | {counts['rows_start']} |
| 2. Rows changed by HTML fix (&lt; &gt; &amp; ...) | {counts['html_rows_changed']} |
| 3. Rows changed by stripping extra spaces | {counts['space_rows_changed']} |
| 4. Exact duplicate messages removed | {counts['duplicates_removed']} |
| Rows after cleaning | {counts['rows_end']} |
| Train rows (80%) | {len(train)} |
| Test rows (20%) | {len(test)} |

Duplicate removal was moved after the HTML fix and space stripping, because cleaning creates new duplicates (6 messages were in both train and test before).

## Class balance

- Before cleaning: {balance(raw_labels)}
- After cleaning: {balance(cleaned['label'])}
- Train: {balance(train['label'])}
- Test: {balance(test['label'])}

## Rule not in the file

**Source:** Cybermalveillance.gouv.fr (the French government's cybersecurity assistance platform), leaflet "L'hameçonnage":
https://www.cybermalveillance.gouv.fr/medias/2026/02/260129_FicheReflexe_Hameconnage.pdf
Consulted on 2 November 2026.

**What it says:** "aucune administration ou société commerciale sérieuse ne vous demandera vos données bancaires ou vos mots de passe par message électronique ou par téléphone."
(No serious administration or company will ever ask for your bank details or passwords by message or by phone.)

**The rule I apply:** a message that asks the reader for bank details, a password, or a payment through a link is treated as a scam, whoever claims to send it (bank, Ameli, CAF, Colissimo...).

**Why it's needed:** the dataset only says spam or ham, never why. This rule gives a reason that comes from an official source, not from the data. It is used in tools/tactics.py and check_sms to flag these requests, and it is what the explanation shown to the user is based on.
"""
    (DATA / "cleaning_log.md").write_text(log, encoding="utf-8")


if __name__ == "__main__":
    raw = pd.read_csv(DATA / "raw" / "sms.tsv", sep="\t", quoting=csv.QUOTE_NONE)
    cleaned, counts = clean(raw)
    train, test = split(cleaned)
    train.to_csv(DATA / "train.csv", index=False)
    test.to_csv(DATA / "test.csv", index=False)
    write_log(counts, raw, cleaned, train, test)
    print(counts)
