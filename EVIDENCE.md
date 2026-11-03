# Evidence

One section per block: what it shows, which files, and the command to reproduce it.
Commands are run from the project folder. "(llama-server)" means llama-server must be running.

## Block 1: My own tool, called by Qwen

**What it shows:** Qwen calls my tool `check_sms(text)` (OpenAI tools format), my code runs it,
sends the result back, and Qwen writes the answer from it.

**Files:** tools/check_sms.py, agent/loop.py, traces/20261102-165255-824920.json

**Saved trace of a real call** (traces/20261102-165255-824920.json, 16:52:51 -> 16:52:55):
- SMS from the dataset: "SPJanuary Male Sale! Hot Gay chat now cheaper, call 08709222922. ..."
- Round 1: Qwen calls `check_sms` with the full SMS as `text`.
- Tool result: is_scam true, scam_probability 0.819, tactics ["urgency"],
  links ["08709222922", "08712460324"], asks_for_sensitive false.
- Final answer: "Verdict: scam / Probability: 81.9% / Tricks: urgency / Why: This message tricks
  you into spending money on unwanted adult calls by pretending to offer a big discount."
  No phone number repeated.

Note: this trace was made before I removed the probability from the answer and before the guard
was added, so it has a "Probability" line and no "guard" section. Traces with the current version:
traces/bench/B_*.json.

**Reproduce (llama-server):** `python -m agent.loop` (writes 2 new traces in traces/; answers can
differ, temperature 0.7)

## Block 3: Rule enforced in code (the guard)

**What it shows:** the guard checks Qwen's final answer in code, not in the prompt. It blocks the
answer if (a) it names a trick (urgency, fake authority, reward, fear, or the French words) that
`check_sms` did not detect, (b) it contains a URL or phone number, or if the answer is empty or
`check_sms` was not called. If blocked, Qwen gets one more try with the reasons; if still blocked,
the user gets a safe fallback built only from the tool result. Every decision is saved in the
trace under "guard".

**Files:** agent/guard.py, agent/loop.py (guard + fallback), tests/test_guard.py

**Tests that try to break it** (tests/test_guard.py, 7 tests): "fear" when tactics is ["urgency"]
-> blocked; same in French ("peur") -> blocked; "bit.ly/abc" -> blocked; "0612345678" -> blocked;
a correct reply -> passes; no tool call -> blocked; the fallback always passes the guard.

**Real case:** benchmark task 10 ("Actually getting ready to leave the house.", ham),
traces/bench/B_run1_task10.json, B_run2_task10.json, B_run3_task10.json. Qwen did not call
check_sms in any of the 3 runs, the guard blocked with reason "check_sms was not called", and the
answer was replaced by the fallback "Verdict: unknown". Explained in bench/results.md.

**Reproduce:** `python -m pytest tests/test_guard.py`

## Block 4: Qwen as a judge

**What it shows:** Qwen answers "Is this SMS a scam? Answer only yes or no." with max_tokens=1,
logprobs and top_logprobs=10, thinking off. P(yes) = p_yes / (p_yes + p_no), read from the
logprobs ("yes", "Yes", " yes"... added together). Tested on 100 messages from data/test.csv
(50 spam, 50 ham, random_state=42). No yes/no in the top 10 tokens: 0 messages.

| Threshold | Misses (scam judged safe) | False alarms (safe judged scam) |
|---|---|---|
| 0.3 | 0 | 31 |
| 0.5 | 5 | 20 |
| 0.7 | 12 | 7 |
| 0.9 | 35 | 1 |

Chosen threshold: 0.5 (reasons and limitations in judge/report.md, "Threshold I chose").

**Files:** judge/qwen_judge.py, judge/scores.csv, judge/report.md

**Reproduce (llama-server):** `python judge/qwen_judge.py raw` (one raw API response with the
logprobs), then `python judge/qwen_judge.py`

## Block 6: Data cleaning with a log, plus one rule not in the data

**What it shows:** the SMS Spam Collection cleaned step by step, with counts, before a
stratified 80/20 split (random_state=42). Data source used: the GitHub mirror (the UCI download
failed), read with csv.QUOTE_NONE so that SMS containing a quote are not merged (5,574 rows, not
5,572).

| Step | Count |
|---|---|
| 1. Rows at start | 5574 |
| 2. Rows changed by HTML fix (&lt; &gt; &amp; ...) | 309 |
| 3. Rows changed by stripping extra spaces | 424 |
| 4. Exact duplicate messages removed | 414 |
| Rows after cleaning | 5160 |
| Train / test | 4128 / 1032 |

Class balance: before ham 86.6% / spam 13.4%; after 87.6% / 12.4%; train 87.5% / 12.5%;
test 87.6% / 12.4%. Duplicate removal was moved after the HTML fix and space stripping because
cleaning creates new duplicates (6 messages were in both train and test before). A test checks
that train.csv and test.csv share 0 messages.

**Rule not in the data:** from Cybermalveillance.gouv.fr ("L'hameçonnage" leaflet): no serious
administration or company asks for bank details or passwords by message. Implemented as
`asks_for_sensitive()` in tools/tactics.py (sensitive word + link); if True, `check_sms` says scam
whatever the classifier says. Source, quote and reasoning in data/cleaning_log.md.

**Files:** data/download.py, data/clean.py, data/cleaning_log.md, tests/test_clean.py,
tools/tactics.py, tests/test_tactics.py

**Reproduce:** `python data/download.py`, `python data/clean.py`,
`python -m pytest tests/test_clean.py tests/test_tactics.py`

## Block 7: My own classifier (TF-IDF + Naive Bayes)

**What it shows:** a scikit-learn pipeline (TfidfVectorizer + MultinomialNB) trained on
data/train.csv only, evaluated once on the held-out data/test.csv (1032 rows), against the
"always ham" baseline. The threshold 0.11 was chosen on train.csv with 5-fold cross-validation
(lowest threshold keeping precision >= 0.9), not on the test set.

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| TF-IDF + NB, threshold 0.5 | 0.951 | 1.000 | 0.602 | 0.751 |
| TF-IDF + NB, threshold 0.11 | 0.965 | 0.843 | 0.883 | 0.863 |
| Always ham (baseline) | 0.876 | 0.000 | 0.000 | 0.000 |

Confusion matrix at 0.11: real ham 883 OK / 21 false alarms; real spam 15 missed / 113 caught.
Confusion matrices for all three rows in model/report.md. Trained with scikit-learn 1.9.1
(pinned in requirements.txt).

**Files:** model/train.py, model/report.md, tests/test_model.py

**Reproduce:** `python model/train.py`, `python -m pytest tests/test_model.py`

## Block 9: Benchmark

Source: bench/results.md, made by `python -m bench.run`. Traces: traces/bench/ (180 files).

- 30 tasks from data/test.csv (15 spam, 15 ham, random_state=7), bench/tasks.json
- 3 runs per setup, temperature 0.7, thinking off
- A) Qwen alone: "Is this SMS a scam? Answer yes or no."
- B) Full system: agent loop (check_sms tool + guard)

| Setup | Run 1 | Run 2 | Run 3 | Mean | Std |
|---|---|---|---|---|---|
| A) Qwen alone | 0.667 | 0.533 | 0.633 | 0.611 | 0.069 |
| B) Full system | 0.967 | 0.967 | 0.967 | 0.967 | 0.000 |

- A got 16 different tasks wrong at least once (13 ham, 3 spam).
- B got 1 task wrong: task 10 (ham), in 3/3 runs.
- Failure explained: task 10, see "Failure explained" in bench/results.md
  (traces/bench/B_run1_task10.json, B_run2_task10.json, B_run3_task10.json).

## Extra: scam tricks detector

**What it shows:** `detect_tactics()` (keyword lists, English and French, whole words) compared
with labels suggested by Claude and checked/edited by me (rows 2, 9, 14, 18 were my calls) on 30 messages from data/test.csv (20 spam, 10 ham),
bench/tactics_labels.csv.

| Trick | Labelled | Detected | Both | Precision | Recall |
|---|---|---|---|---|---|
| urgency | 6 | 8 | 5 | 0.62 | 0.83 |
| fake_authority | 1 | 0 | 0 | n/a | 0.00 |
| reward | 12 | 8 | 6 | 0.75 | 0.50 |
| fear | 0 | 0 | 0 | n/a | n/a |

13 of the 30 messages have a mismatch, all listed in tools/tactics_report.md. Fear never appears
in my labels, so it cannot be measured on this sample.

**Files:** tools/tactics.py, tools/tactics_eval.py, bench/tactics_labels.csv,
tools/tactics_report.md, tests/test_tactics.py

**Reproduce:** `python -m tools.tactics_eval`
