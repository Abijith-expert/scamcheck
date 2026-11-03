"""Qwen as a judge: P(yes) for "Is this SMS a scam?", read from the token logprobs.

python judge/qwen_judge.py raw   -> prints one raw API response and stops
python judge/qwen_judge.py       -> scores 100 test messages and writes the report
"""
import math
import sys
from pathlib import Path

import pandas as pd
from openai import OpenAI

ROOT = Path(__file__).parent.parent
QUESTION = "Is this SMS a scam? Answer only yes or no."
THRESHOLDS = [0.3, 0.5, 0.7, 0.9]

# llama-server does not check the key, but the client needs one
client = OpenAI(base_url="http://localhost:8080/v1", api_key="none")


def ask(sms):
    """Ask Qwen for exactly one token, with the 10 most likely tokens and their logprobs."""
    return client.chat.completions.create(
        model="qwen",
        messages=[{"role": "user", "content": f"{QUESTION}\n\nSMS: {sms}"}],
        max_tokens=1,
        logprobs=True,
        top_logprobs=10,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )


def p_yes(sms):
    """P(yes) = p_yes / (p_yes + p_no), or None if neither yes nor no is in the top 10."""
    logprobs = ask(sms).choices[0].logprobs
    if logprobs is None:
        raise RuntimeError("llama-server returned no logprobs, stopping")
    top = logprobs.content[0].top_logprobs

    # "yes", "Yes", " yes", "YES" all count as yes (same for no)
    yes = sum(math.exp(t.logprob) for t in top if t.token.strip().lower() == "yes")
    no = sum(math.exp(t.logprob) for t in top if t.token.strip().lower() == "no")
    if yes + no == 0:
        return None
    return yes / (yes + no)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "raw":
        print(ask("URGENT! Your parcel is blocked, pay 1.99 EUR here: http://example.com").model_dump_json(indent=2))
        sys.exit()

    test = pd.read_csv(ROOT / "data" / "test.csv")
    sample = test.groupby("label").sample(50, random_state=42)  # 50 spam + 50 ham
    sample["p_yes"] = [p_yes(sms) for sms in sample["message"]]
    sample.to_csv(ROOT / "judge" / "scores.csv", index=False)

    scored = sample.dropna(subset=["p_yes"])
    no_answer = len(sample) - len(scored)

    rows = ""
    for t in THRESHOLDS:
        judged_scam = scored["p_yes"] >= t
        misses = int(((scored["label"] == 1) & ~judged_scam).sum())
        false_alarms = int(((scored["label"] == 0) & judged_scam).sum())
        rows += f"| {t} | {misses} | {false_alarms} |\n"

    report = f"""# Qwen as a judge

Question: "{QUESTION}" (thinking off, max_tokens=1, top_logprobs=10).
P(yes) = p_yes / (p_yes + p_no), read from the logprobs of the first token.
A message is judged scam when P(yes) >= threshold.

Messages: {len(sample)} from data/test.csv (50 spam, 50 ham, random_state=42).
No yes/no in the top 10 tokens (P(yes) = None): {no_answer}, left out of the table below.

| Threshold | Misses (scam judged safe) | False alarms (safe judged scam) |
|---|---|---|
{rows}
## Threshold I chose

I chose 0.5. For my users (people like my grandparents) a missed scam is worse than a false alarm, the same rule I used for the classifier. 0.5 misses 5 of 50 scams (10%); 0.7 makes fewer errors overall but misses 12 (24%), one scam in four, which I don't accept. 0.3 catches every scam but flags 31 of 50 normal messages, nobody would keep using it.

Limitations: the threshold was chosen on these same 100 messages, so the numbers are optimistic. The sample is 50/50 but real SMS are about 12% scams, so with a 40% false-alarm rate most alerts would be wrong. My trained classifier does much better (recall 0.88, precision 0.84 on the test set). Qwen alone is a weak judge; that is why my system gives it the classifier as a tool (compared in the benchmark, block 9).
"""
    (ROOT / "judge" / "report.md").write_text(report, encoding="utf-8")
    print(report)
