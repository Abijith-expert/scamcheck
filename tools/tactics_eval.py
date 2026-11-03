"""Compare detect_tactics() with my hand labels in bench/tactics_labels.csv.
Run from the project folder: python -m tools.tactics_eval

In the "tactics" column write the tricks separated by ";" (e.g. urgency;reward),
or "none" if the message uses none of them.
"""
from pathlib import Path

import pandas as pd

from tools.tactics import TACTICS, detect_tactics

ROOT = Path(__file__).parent.parent

if __name__ == "__main__":
    labels = pd.read_csv(ROOT / "bench" / "tactics_labels.csv")
    if labels["tactics"].isna().any():
        raise SystemExit("Some rows are not labelled yet (write 'none' if there is no trick).")

    rows = ""
    for name in TACTICS:
        true = labels["tactics"].apply(lambda t: name in t.split(";"))
        pred = labels["message"].apply(lambda m: name in detect_tactics(m))
        tp = int((true & pred).sum())
        precision = f"{tp / pred.sum():.2f}" if pred.sum() > 0 else "n/a"
        recall = f"{tp / true.sum():.2f}" if true.sum() > 0 else "n/a"
        rows += f"| {name} | {int(true.sum())} | {int(pred.sum())} | {tp} | {precision} | {recall} |\n"

    # every row where my labels and detect_tactics() do not agree
    mismatches = ""
    for i, row in labels.iterrows():
        mine = sorted(name for name in row["tactics"].split(";") if name != "none")
        found = sorted(detect_tactics(row["message"]))
        if mine != found:
            message = row["message"][:60].replace("|", "/")  # "|" would break the table
            mismatches += f"| {i + 1} | {message} | {', '.join(mine) or 'none'} | {', '.join(found) or 'none'} |\n"

    report = f"""# Tactics detection report

{len(labels)} messages from data/test.csv ({(labels["label"] == "spam").sum()} spam, {(labels["label"] == "ham").sum()} ham), labels suggested by Claude and checked/edited by me
(rows 2, 9, 14, 18 were my calls) in bench/tactics_labels.csv,
compared with detect_tactics() in tools/tactics.py.

| Trick | Labelled | Detected | Both | Precision | Recall |
|---|---|---|---|---|---|
{rows}
## Mismatches

Row = position in bench/tactics_labels.csv (1 = first message).

| Row | Message (first 60 chars) | My label | detect_tactics found |
|---|---|---|---|
{mismatches}
## What this shows

The keyword detector is weak: urgency precision 0.62 ("now" also appears in normal messages, like row 29 "Now press conference"), reward recall 0.50 (whole-word matching catches "won" but not "win" or "awarded"), and it never found fake authority ("customer service" and "delivery" are not in my lists). Fear could not be measured: no message in this 2011 UK sample uses it.

For my system, precision matters more than recall: the guard only lets Qwen name tricks the detector found, so a missed trick makes the explanation shorter, while a wrong trick shows the user a false reason (example: in traces/20261102-170318-615467.json, "now" was detected as urgency and Qwen wrote "pressure to call immediately", which the message doesn't say).

I did not change the word lists after seeing these results, because tuning them on the same 30 messages would make the score look better than it is on new messages. Improvement for later: word variants (win/award/awarded) and checking on a new labelled sample.
"""
    (ROOT / "tools" / "tactics_report.md").write_text(report, encoding="utf-8")
    print(report)
