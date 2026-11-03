# Benchmark results

30 tasks from bench/tasks.json (15 spam), 3 runs per setup, temperature 0.7.

- A) Qwen alone: "Is this SMS a scam? Answer yes or no."
- B) Full system: agent loop (check_sms tool + guard), verdict read from "Verdict: scam/safe".

A reply with no clear yes/no (A) or no verdict (B) counts as wrong.
Every trace is in traces/bench/ (e.g. B_run2_task07.json = setup B, run 2, task 7).

## Accuracy

| Setup | Run 1 | Run 2 | Run 3 | Mean | Std |
|---|---|---|---|---|---|
| A) Qwen alone | 0.667 | 0.533 | 0.633 | 0.611 | 0.069 |
| B) Full system | 0.967 | 0.967 | 0.967 | 0.967 | 0.000 |

## Tasks each setup got wrong

### A) Qwen alone

| Task | Real label | Wrong in | Message (first 60 chars) |
|---|---|---|---|
| 1 | ham | 3/3 runs | Hi dear we saw dear. We both are happy. Where you my battery |
| 2 | ham | 3/3 runs | Hey you gave them your photo when you registered for driving |
| 4 | ham | 1/3 runs | Should i buy him a blackberry bold 2 or torch. Should i buy  |
| 5 | ham | 3/3 runs | I gotta collect da car at 6 lei. |
| 6 | ham | 2/3 runs | Damn, poor zac doesn't stand a chance |
| 7 | ham | 3/3 runs | Sez, hows u & de arab boy? Hope u r all good give my love 2  |
| 8 | ham | 2/3 runs | WOT U UP 2 J? |
| 9 | ham | 2/3 runs | Is that what time you want me to come? |
| 11 | ham | 2/3 runs | "NOT ENUFCREDEIT TOCALL.SHALL ILEAVE UNI AT 6 +GET A BUS TO  |
| 12 | ham | 3/3 runs | Dai what this da.. Can i send my resume to this id. |
| 13 | ham | 2/3 runs | Huh so slow i tot u reach long ago liao... U 2 more days onl |
| 14 | ham | 2/3 runs | It,,s a taxt massage....tie-pos argh ok! Lool! |
| 15 | ham | 3/3 runs | Found it, ENC <#> , where you at? |
| 21 | spam | 1/3 runs | 100 dating service cal;l 09064012103 box334sk38ch |
| 26 | spam | 1/3 runs | Get a brand new mobile phone by being an agent of The Mob! P |
| 27 | spam | 2/3 runs | Hungry gay guys feeling hungry and up 4 it, now. Call 087187 |

### B) Full system

| Task | Real label | Wrong in | Message (first 60 chars) |
|---|---|---|---|
| 10 | ham | 3/3 runs | Actually getting ready to leave the house. |


## Failure explained

Task 10, "Actually getting ready to leave the house." (ham), wrong in 3/3 runs of the full system (traces/bench/B_run1_task10.json, B_run2_task10.json, B_run3_task10.json).

In all three runs Qwen did not call check_sms (tool_calls is empty). It treated the SMS as if I was talking to it, not as a message to check: run 1 "I cannot check an SMS message because you haven't provided the text", run 2 "Could you please provide the text of the SMS", run 3 "I am not your grandmother, and I am ready to leave the house!".

My guard blocks any answer when check_sms was not called (reason: "check_sms was not called"), so all three answers were replaced by the fallback "Verdict: unknown", which the benchmark counts as wrong.

This is the safety rule working as intended: the system says "unknown" instead of giving a verdict that nothing checked. The cause is that a short, ordinary sentence looks like a chat message to Qwen.

Possible fix, not applied so I don't tune on the benchmark tasks: when the model doesn't call the tool, the loop could call check_sms itself and only ask Qwen to write the explanation.