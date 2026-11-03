# Classifier report

Trained on data/train.csv (4128 rows), evaluated only on data/test.csv (1032 rows).
Precision, recall and F1 are for the spam class.

The threshold 0.11 was chosen on train.csv with 5-fold cross-validation
(lowest threshold keeping precision >= 0.9), not on test.csv.

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| TF-IDF + NB, threshold 0.5 | 0.951 | 1.000 | 0.602 | 0.751 |
| TF-IDF + NB, threshold 0.11 | 0.965 | 0.843 | 0.883 | 0.863 |
| Always ham (baseline) | 0.876 | 0.000 | 0.000 | 0.000 |

## Confusion matrix: TF-IDF + NB, threshold 0.5

| | predicted ham | predicted spam |
|---|---|---|
| real ham | 904 | 0 |
| real spam | 51 | 77 |

## Confusion matrix: TF-IDF + NB, threshold 0.11

| | predicted ham | predicted spam |
|---|---|---|
| real ham | 883 | 21 |
| real spam | 15 | 113 |

## Confusion matrix: Always ham (baseline)

| | predicted ham | predicted spam |
|---|---|---|
| real ham | 904 | 0 |
| real spam | 128 | 0 |
