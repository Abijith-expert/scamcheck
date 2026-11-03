"""Download the UCI SMS Spam Collection into data/raw/sms.tsv."""
import csv
from pathlib import Path

import pandas as pd

RAW_FILE = Path(__file__).parent / "raw" / "sms.tsv"
MIRROR = "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv"


def from_uci():
    from ucimlrepo import fetch_ucirepo
    df = fetch_ucirepo(id=228).data.original.iloc[:, :2]
    df.columns = ["label", "message"]
    if not set(df["label"]) <= {"ham", "spam"}:
        raise ValueError("unexpected format from UCI")
    return df


def from_mirror():
    # QUOTE_NONE: some SMS contain " and pandas would otherwise merge two lines
    return pd.read_csv(MIRROR, sep="\t", header=None, names=["label", "message"],
                       quoting=csv.QUOTE_NONE)


if __name__ == "__main__":
    try:
        df = from_uci()
        print("Downloaded from UCI")
    except Exception as error:
        print(f"UCI failed ({error}), using the GitHub mirror")
        df = from_mirror()
    RAW_FILE.parent.mkdir(exist_ok=True)
    df.to_csv(RAW_FILE, sep="\t", index=False, quoting=csv.QUOTE_NONE)
    print(f"Saved {len(df)} rows to {RAW_FILE}")
