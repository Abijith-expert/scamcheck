"""Benchmark: A) Qwen alone vs B) my full system (agent loop + guard).
3 runs each on the 30 tasks of bench/tasks.json, temperature 0.7.

python -m bench.run           -> full benchmark, writes bench/results.md
python -m bench.run --quick   -> 3 tasks, 1 run, traces in traces/bench_quick/, only prints
"""
import os

# Must run BEFORE numpy / scikit-learn are imported: with llama-server using most of the RAM,
# OpenBLAS starting one thread per CPU core can crash with "Memory allocation still failed".
# One thread is enough here. setdefault keeps any value already set in the terminal.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import json
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

from agent.loop import NO_THINKING, client, run

ROOT = Path(__file__).parent.parent
TRACES = ROOT / "traces" / "bench"              # real benchmark evidence
QUICK_TRACES = ROOT / "traces" / "bench_quick"  # --quick tests, gitignored
TEMPERATURE = 0.7
QUESTION = "Is this SMS a scam? Answer yes or no."


def qwen_alone(sms, trace_name, trace_dir):
    """Setup A: ask Qwen directly. Returns 1 (scam), 0 (safe) or None (no clear answer)."""
    started = datetime.now().isoformat(timespec="seconds")
    response = client.chat.completions.create(
        model="qwen", messages=[{"role": "user", "content": f"{QUESTION}\n\nSMS: {sms}"}],
        temperature=TEMPERATURE, extra_body=NO_THINKING)
    answer = response.choices[0].message.content or ""
    first_word = answer.strip().lower()
    prediction = 1 if first_word.startswith("yes") else 0 if first_word.startswith("no") else None

    trace = {"started": started, "setup": "A", "sms": sms, "question": QUESTION,
             "answer": answer, "prediction": prediction,
             "finished": datetime.now().isoformat(timespec="seconds")}
    trace_dir.mkdir(parents=True, exist_ok=True)
    (trace_dir / f"{trace_name}.json").write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")
    return prediction


def full_system(sms, trace_name, trace_dir):
    """Setup B: the agent loop, then read "Verdict: scam/safe" from its answer."""
    trace = run(sms, temperature=TEMPERATURE, trace_dir=trace_dir, trace_name=trace_name)
    answer = trace["final_answer"] or ""
    match = re.search(r"verdict:\s*(scam|safe)", answer, re.IGNORECASE)
    if match is None:
        return None
    return 1 if match.group(1).lower() == "scam" else 0


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    tasks = json.loads((ROOT / "bench" / "tasks.json").read_text(encoding="utf-8"))
    n_runs = 3
    trace_dir = TRACES
    if quick:  # separate folder, so a quick test can never overwrite the real traces
        tasks, n_runs, trace_dir = tasks[:3], 1, QUICK_TRACES

    setups = {"A": ("Qwen alone", qwen_alone), "B": ("Full system", full_system)}
    accuracies = {"A": [], "B": []}
    wrong = {"A": {}, "B": {}}  # task id -> number of runs where it was wrong

    for key, (name, predict) in setups.items():
        for r in range(1, n_runs + 1):
            correct = 0
            for i, task in enumerate(tasks, start=1):
                prediction = predict(task["message"], f"{key}_run{r}_task{task['id']:02d}", trace_dir)
                ok = prediction == task["label"]  # None (no clear answer) counts as wrong
                correct += ok
                if not ok:
                    wrong[key][task["id"]] = wrong[key].get(task["id"], 0) + 1
                print(f"[{key}] run {r}/{n_runs} task {i}/{len(tasks)}: "
                      f"predicted {prediction}, real {task['label']} {'OK' if ok else 'WRONG'}")
            accuracies[key].append(correct / len(tasks))
            print(f"[{key}] run {r} accuracy: {accuracies[key][-1]:.3f}\n")

    # summary table
    run_headers = " | ".join(f"Run {r}" for r in range(1, n_runs + 1))
    table = f"| Setup | {run_headers} | Mean | Std |\n|---|" + "---|" * (n_runs + 2) + "\n"
    for key, (name, _) in setups.items():
        accs = accuracies[key]
        std = statistics.stdev(accs) if len(accs) > 1 else 0.0
        table += f"| {key}) {name} | " + " | ".join(f"{a:.3f}" for a in accs)
        table += f" | {statistics.mean(accs):.3f} | {std:.3f} |\n"

    # wrong tasks per setup
    messages = {task["id"]: task for task in tasks}
    wrong_lists = ""
    for key, (name, _) in setups.items():
        wrong_lists += f"\n### {key}) {name}\n\n"
        if not wrong[key]:
            wrong_lists += "No task wrong.\n"
            continue
        wrong_lists += "| Task | Real label | Wrong in | Message (first 60 chars) |\n|---|---|---|---|\n"
        for task_id in sorted(wrong[key]):
            task = messages[task_id]
            label = "spam" if task["label"] == 1 else "ham"
            text = task["message"][:60].replace("|", "/")
            wrong_lists += f"| {task_id} | {label} | {wrong[key][task_id]}/{n_runs} runs | {text} |\n"

    results = f"""# Benchmark results

{len(tasks)} tasks from bench/tasks.json ({sum(t['label'] for t in tasks)} spam), {n_runs} runs per setup, temperature {TEMPERATURE}.

- A) Qwen alone: "{QUESTION}"
- B) Full system: agent loop (check_sms tool + guard), verdict read from "Verdict: scam/safe".

A reply with no clear yes/no (A) or no verdict (B) counts as wrong.
Every trace is in traces/bench/ (e.g. B_run2_task07.json = setup B, run 2, task 7).

## Accuracy

{table}
## Tasks each setup got wrong
{wrong_lists}
## Failure explained

Task 10, "Actually getting ready to leave the house." (ham), wrong in 3/3 runs of the full system (traces/bench/B_run1_task10.json, B_run2_task10.json, B_run3_task10.json).

In all three runs Qwen did not call check_sms (tool_calls is empty). It treated the SMS as if I was talking to it, not as a message to check: run 1 "I cannot check an SMS message because you haven't provided the text", run 2 "Could you please provide the text of the SMS", run 3 "I am not your grandmother, and I am ready to leave the house!".

My guard blocks any answer when check_sms was not called (reason: "check_sms was not called"), so all three answers were replaced by the fallback "Verdict: unknown", which the benchmark counts as wrong.

This is the safety rule working as intended: the system says "unknown" instead of giving a verdict that nothing checked. The cause is that a short, ordinary sentence looks like a chat message to Qwen.

Possible fix, not applied so I don't tune on the benchmark tasks: when the model doesn't call the tool, the loop could call check_sms itself and only ask Qwen to write the explanation.
"""
    print(results)
    if quick:
        print("(--quick: bench/results.md not written)")
    else:
        (ROOT / "bench" / "results.md").write_text(results, encoding="utf-8")
