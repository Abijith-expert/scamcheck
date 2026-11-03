from pathlib import Path

import pandas as pd

from data.clean import clean, split

# 6 rows: one exact duplicate, one &amp;, one with extra spaces
FIXTURE = pd.DataFrame({
    "label": ["ham", "ham", "ham", "ham", "spam", "spam"],
    "message": [
        "Hi mum",
        "Hi mum",
        "See you at 5 &amp; bring food",
        "  Ok   see you  ",
        "WIN a free prize now",
        "URGENT your account is blocked",
    ],
})


def test_duplicates_removed():
    cleaned, counts = clean(FIXTURE)
    assert counts["duplicates_removed"] == 1
    assert len(cleaned) == 5


def test_amp_becomes_and():
    cleaned, counts = clean(FIXTURE)
    assert "See you at 5 & bring food" in list(cleaned["message"])
    assert counts["html_rows_changed"] == 1


def test_no_message_in_both_train_and_test():
    cleaned, _ = clean(FIXTURE)
    # 0.4 instead of 0.2: with only 5 rows, 20% is too small to hold both classes
    train, test = split(cleaned, test_size=0.4)
    assert set(train["message"]) & set(test["message"]) == set()


def test_real_train_and_test_share_no_message():
    # needs data/clean.py to have been run first
    data = Path(__file__).parent.parent / "data"
    train = pd.read_csv(data / "train.csv")
    test = pd.read_csv(data / "test.csv")
    assert set(train["message"]) & set(test["message"]) == set()
