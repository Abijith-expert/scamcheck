# Tactics detection report

30 messages from data/test.csv (20 spam, 10 ham), labels suggested by Claude and checked/edited by me
(rows 2, 9, 14, 18 were my calls) in bench/tactics_labels.csv,
compared with detect_tactics() in tools/tactics.py.

| Trick | Labelled | Detected | Both | Precision | Recall |
|---|---|---|---|---|---|
| urgency | 6 | 8 | 5 | 0.62 | 0.83 |
| fake_authority | 1 | 0 | 0 | n/a | 0.00 |
| reward | 12 | 8 | 6 | 0.75 | 0.50 |
| fear | 0 | 0 | 0 | n/a | n/a |

## Mismatches

Row = position in bench/tactics_labels.csv (1 = first message).

| Row | Message (first 60 chars) | My label | detect_tactics found |
|---|---|---|---|
| 3 | New TEXTBUDDY Chat 2 horny guys in ur area 4 just 25p Free 2 | none | reward |
| 4 | Customer service announcement. We recently tried to make a d | fake_authority | none |
| 5 | Dear 0776xxxxxxx U've been invited to XCHAT. This is our fin | urgency | none |
| 6 | Ur cash-balance is currently 500 pounds - to maximize ur cas | reward, urgency | urgency |
| 7 | YOUR CHANCE TO BE ON A REALITY FANTASY SHOW call now = 08707 | reward, urgency | urgency |
| 8 | Camera - You are awarded a SiPix Digital Camera! call 090612 | reward | none |
| 10 | we tried to contact you re your response to our offer of a n | reward | none |
| 13 | Promotion Number: 8714714 - UR awarded a City Break and coul | reward | none |
| 16 | Rock yr chik. Get 100's of filthy films &XXX pics on yr phon | none | urgency |
| 18 | No 1 POLYPHONIC tone 4 ur mob every week! Just txt PT2 to 87 | reward | reward, urgency |
| 19 | u r subscribed 2 TEXTCOMP 250 wkly comp. 1st wk?s free quest | none | reward |
| 20 | WOW! The Boys R Back. TAKE THAT 2007 UK Tour. Win VIP Ticket | reward | none |
| 29 | Now press conference da:) | none | urgency |

## What this shows

The keyword detector is weak: urgency precision 0.62 ("now" also appears in normal messages, like row 29 "Now press conference"), reward recall 0.50 (whole-word matching catches "won" but not "win" or "awarded"), and it never found fake authority ("customer service" and "delivery" are not in my lists). Fear could not be measured: no message in this 2011 UK sample uses it.

For my system, precision matters more than recall: the guard only lets Qwen name tricks the detector found, so a missed trick makes the explanation shorter, while a wrong trick shows the user a false reason (example: in traces/20261102-170318-615467.json, "now" was detected as urgency and Qwen wrote "pressure to call immediately", which the message doesn't say).

I did not change the word lists after seeing these results, because tuning them on the same 30 messages would make the score look better than it is on new messages. Improvement for later: word variants (win/award/awarded) and checking on a new labelled sample.
