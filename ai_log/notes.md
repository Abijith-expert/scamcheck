# AI-use notes: building ScamCheck with Claude

One AI coding session with Claude. I decided what to build, what to clean and what to measure;
Claude wrote and ran the code. Claude could not reach llama-server on my laptop, so every real
Qwen run (smoke test, judge, agent loop, benchmark) was done by me on my laptop.

## 1. Setup

- Kept as is: the folder layout, requirements.txt, .gitignore, the README start, the ai_log README,
  and smoke_test.py (thinking turned off with `chat_template_kwargs: enable_thinking False`).
- Corrected or decided by me: added `.venv/` to .gitignore. After an InconsistentVersionWarning
  (model pickled with scikit-learn 1.7.2, my laptop has 1.9.1) I retrained on my laptop and pinned
  `scikit-learn==1.9.1` so a fresh clone uses the same version; added "Requires Python 3.11+".
- Prompt rewritten: none.

## 2. Data cleaning (block 6)

- Kept as is: download.py (UCI with the GitHub mirror as fallback), the structure of clean.py,
  the cleaning log written by the script, the 6-row test fixture.
- Corrected or decided by me:
  - The data had 5,572 rows instead of 5,574. I suspected that SMS containing `"` were merged with
    the next line, and asked to read with `csv.QUOTE_NONE`: that gave 5,574.
  - Claude found that cleaning created new duplicates (6 messages in both train and test). I
    decided to move duplicate removal after the HTML fix and space stripping.
  - I asked for a test that train.csv and test.csv share no message on the real data, the step
    numbers renumbered in the real order, and the space-stripping row (424 rows) added back.
  - I wrote the "Rule not in the file" section myself from cybermalveillance.gouv.fr and asked
    Claude not to make up a rule.
- Prompt rewritten: none.

## 3. Classifier (block 7)

- Kept as is: the TF-IDF + Multinomial Naive Bayes pipeline, the report written by train.py,
  predict_proba(), the always-ham baseline.
- Corrected or decided by me: recall 0.60 at threshold 0.5 was too low, because for my users a
  missed scam is worse than a false alarm. I did not want to pick the threshold on the test set
  (leakage), so I asked for 5-fold cross_val_predict on train only, lowest threshold keeping
  precision >= 0.90. It gave 0.11. Test precision came out 0.843, below 0.90, and I kept it instead
  of tuning on the test set.
- Prompt rewritten: none.

## 4. Qwen as a judge (block 4)

- Kept as is: qwen_judge.py (P(yes) from top_logprobs, "yes"/"Yes"/" yes" added together, None
  when neither appears, the `raw` mode).
- Corrected or decided by me: I asked to see a raw API response first and to stop instead of
  faking it if the logprobs did not come back. I ran it on my laptop (100 messages, 0 None).
  I chose the threshold 0.5 and wrote the "Threshold I chose" explanation and its limitations
  myself.
- Prompt rewritten: none (the judge question is the one I gave at the start).

## 5. Tricks detector

- Kept as is: tools/tactics.py with whole-word matching, detect_links(), tactics_eval.py and the
  mismatch table.
- Corrected or decided by me:
  - The four word lists (English and French) are mine. I asked for the rule asks_for_sensitive()
    (sensitive word + link) and that it makes the verdict scam whatever the classifier says.
  - The labels in bench/tactics_labels.csv were suggested by Claude and checked/edited by me
    (rows 2, 9, 14, 18 were my calls). I asked to add 10 ham messages so false alarms show up.
  - I did not change the word lists after seeing the results, so the score is not tuned on the
    same 30 messages. I wrote the "What this shows" section myself.
- Prompt rewritten: none.

## 6. Tool + agent loop (block 1)

- Kept as is: the loop (max 3 rounds, tool result sent back with its tool_call_id), the tool
  described in the OpenAI tools format, the JSON traces in traces/.
- Corrected or decided by me: check_sms returns scam_probability, tactics and links; Claude kept
  is_scam and asks_for_sensitive so my cybermalveillance rule keeps working. Only dataset messages
  go in traces, never real personal SMS.
- Prompt rewritten: the system prompt. The first version asked for "Probability: X". I had it
  replaced by "Flagged by: ..." and "Do not give the probability as a number": I wanted only the
  verdict and what flagged it, not a raw percentage.
  my reason: the classifier threshold is 0.11, so the raw probability is misleading. A real scam can score 15% and still be flagged, and a user reading "Scam, 15%" would not trust it. The verdict comes from my code (threshold + rule), not from the number, so the answer shows what flagged the message instead.

## 7. Guard (block 3)

- Kept as is: agent/guard.py, the retry with the reasons, the fallback built only from the tool
  result, the guard decisions saved in the trace. Claude extended the link check to short links
  like `bit.ly/abc`, which detect_links() would miss.
- Corrected or decided by me: the rule had to be in code, not in the prompt: block a trick that
  check_sms did not detect, and any URL or phone number. Ask the model once more, then fall back.
  I asked for tests that try to break it ("fear" when tactics is ["urgency"], bit.ly/abc,
  0612345678, a correct reply).
- Prompt rewritten: none.

## 8. Benchmark (block 9)

- Kept as is: make_tasks.py (15 spam, 15 ham, random_state=7), run.py, the results table and
  the list of wrong tasks per setup.
- Corrected or decided by me:
  - Setups A (Qwen alone) vs B (full system), 3 runs, temperature 0.7, and a `--quick` flag.
  - `--quick` overwrote 6 real traces (A and B, run 1, tasks 1-3). I asked for --quick to save to
    traces/bench_quick/ (gitignored) and re-ran the full benchmark so all 180 traces match
    results.md.
  - I wrote the "Failure explained" section (task 10: Qwen did not call check_sms, the guard
    replaced the answer with "unknown"). I did not apply the possible fix, to avoid tuning on the
    benchmark tasks.
- Prompt rewritten: none.

## 9. Demo page (app.py)

- Kept as is: the Streamlit page (text box, Check button, big SCAM/SAFE, tricks as tags, the
  Why sentence, the guard note, nothing saved with trace_dir=None).
- Corrected or decided by me: no "Scam probability: X%" on the page, because with the 0.11
  threshold a scam can show 15%; it shows "Flagged by the classifier / the bank-details rule"
  instead. I wrote the French Colissimo example. Streamlit crashed with an OpenBLAS memory error
  while llama-server was running; I found that OPENBLAS_NUM_THREADS=1 fixed it and asked for it
  at the top of app.py, agent/loop.py and bench/run.py.
- Prompt rewritten: none.

## 10. README and EVIDENCE.md

- Kept as is: the structure (what it does, model, setup in a few commands, credits) and one
  EVIDENCE section per block with files and commands.
- Corrected or decided by me: context 8192 and `--device` in the llama-server command, the
  credits (dataset and cybermalveillance.gouv.fr), the wording of who made the tricks labels.
  Only numbers that are really in the repo files.
- Prompt rewritten: none.

## 11. Secrets and personal data check

- Kept as is: the scan results (no keys or passwords, all 184 traces contain only dataset SMS,
  the emails found are inside the public dataset) and the .gitignore additions
  (`.pytest_cache/`, `*.gguf`).
- Corrected or decided by me: nothing deleted without my OK.
- Prompt rewritten: none.

## How I checked AI code

The course's three questions, before keeping code an AI wrote:

1. **Do I know what each line does?**
   I asked for simple, short code with no tricks, and for step-by-step explanations of the loop,
   TF-IDF, why accuracy is misleading and why duplicates go before the split.
   

2. **What happens in the edge case (an empty list, a missing value, a single value)?**
   Examples we handled: no "yes"/"no" in the top 10 tokens -> P(yes) is None and counted;
   logprobs missing -> the judge stops instead of faking; an empty reply or no tool call -> the
   guard blocks; an unlabelled row -> tactics_eval refuses to run; a stratified split on a
   5-row fixture is too small for 20% (test_size=0.4 in the test); std with a single run
   (`--quick`) -> 0.0.

3. **What will I run to check it?**
   `python -m pytest tests` (26 tests), `python -m bench.run --quick` before the full run,
   `python judge/qwen_judge.py raw` to see the logprobs, and checking numbers against their files:
   the benchmark accuracies were recomputed from the 180 traces and match results.md.
