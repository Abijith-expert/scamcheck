# Qwen as a judge

Question: "Is this SMS a scam? Answer only yes or no." (thinking off, max_tokens=1, top_logprobs=10).
P(yes) = p_yes / (p_yes + p_no), read from the logprobs of the first token.
A message is judged scam when P(yes) >= threshold.

Messages: 100 from data/test.csv (50 spam, 50 ham, random_state=42).
No yes/no in the top 10 tokens (P(yes) = None): 0, left out of the table below.

| Threshold | Misses (scam judged safe) | False alarms (safe judged scam) |
|---|---|---|
| 0.3 | 0 | 31 |
| 0.5 | 5 | 20 |
| 0.7 | 12 | 7 |
| 0.9 | 35 | 1 |

## Threshold I chose

I chose 0.5. For my users (people like my grandparents) a missed scam is worse than a false alarm, the same rule I used for the classifier. 0.5 misses 5 of 50 scams (10%); 0.7 makes fewer errors overall but misses 12 (24%), one scam in four, which I don't accept. 0.3 catches every scam but flags 31 of 50 normal messages, nobody would keep using it.

Limitations: the threshold was chosen on these same 100 messages, so the numbers are optimistic. The sample is 50/50 but real SMS are about 12% scams, so with a 40% false-alarm rate most alerts would be wrong. My trained classifier does much better (recall 0.88, precision 0.84 on the test set). Qwen alone is a weak judge; that is why my system gives it the classifier as a tool (compared in the benchmark, block 9).
