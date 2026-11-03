"""Train TF-IDF + Naive Bayes on data/train.csv, pick a threshold with
cross-validation on train only, then evaluate once on data/test.csv."""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (accuracy_score, confusion_matrix, precision_recall_fscore_support,
                             precision_score)
from sklearn.model_selection import cross_val_predict
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).parent.parent
MODEL_FILE = ROOT / "model" / "classifier.pkl"
MIN_PRECISION = 0.90


def scores(y_true, y_pred):
    """Accuracy, then precision / recall / F1 for the spam class (label 1)."""
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", pos_label=1, zero_division=0)
    return accuracy_score(y_true, y_pred), precision, recall, f1


def matrix_table(y_true, y_pred):
    (tn, fp), (fn, tp) = confusion_matrix(y_true, y_pred, labels=[0, 1])
    return f"""| | predicted ham | predicted spam |
|---|---|---|
| real ham | {tn} | {fp} |
| real spam | {fn} | {tp} |
"""


def choose_threshold(y_true, probas):
    """Lowest threshold (0.01, 0.02, ...) whose precision is still >= MIN_PRECISION."""
    for threshold in np.arange(0.01, 1.00, 0.01):
        pred = (probas >= threshold).astype(int)
        if precision_score(y_true, pred, zero_division=0) >= MIN_PRECISION:
            return round(float(threshold), 2)
    return 0.5


def predict_proba(text):
    """Probability (0 to 1) that the text is spam, using the saved model."""
    saved = joblib.load(MODEL_FILE)
    return saved["model"].predict_proba([text])[0][1]


if __name__ == "__main__":
    train = pd.read_csv(ROOT / "data" / "train.csv")
    test = pd.read_csv(ROOT / "data" / "test.csv")
    model = make_pipeline(TfidfVectorizer(), MultinomialNB())

    # 1. choose the threshold on train only: each train message gets a
    #    probability from a model that did not see it (5 folds)
    train_probas = cross_val_predict(model, train["message"], train["label"],
                                     cv=5, method="predict_proba")[:, 1]
    threshold = choose_threshold(train["label"], train_probas)

    # 2. train on all of train.csv and save the model with its threshold
    model.fit(train["message"], train["label"])
    joblib.dump({"model": model, "threshold": threshold}, MODEL_FILE)

    # 3. evaluate once on test.csv
    test_probas = model.predict_proba(test["message"])[:, 1]
    results = [
        ("TF-IDF + NB, threshold 0.5", (test_probas >= 0.5).astype(int)),
        (f"TF-IDF + NB, threshold {threshold}", (test_probas >= threshold).astype(int)),
        ("Always ham (baseline)", [0] * len(test)),
    ]

    rows, matrices = "", ""
    for name, pred in results:
        acc, p, r, f1 = scores(test["label"], pred)
        rows += f"| {name} | {acc:.3f} | {p:.3f} | {r:.3f} | {f1:.3f} |\n"
        matrices += f"\n## Confusion matrix: {name}\n\n{matrix_table(test['label'], pred)}"

    report = f"""# Classifier report

Trained on data/train.csv ({len(train)} rows), evaluated only on data/test.csv ({len(test)} rows).
Precision, recall and F1 are for the spam class.

The threshold {threshold} was chosen on train.csv with 5-fold cross-validation
(lowest threshold keeping precision >= {MIN_PRECISION}), not on test.csv.

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
{rows}{matrices}"""
    (ROOT / "model" / "report.md").write_text(report, encoding="utf-8")
    print(report)
