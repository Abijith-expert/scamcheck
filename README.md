# ScamCheck

Paste an SMS and ScamCheck tells you if it is a **scam** or **safe**, what flagged it
(my trained classifier and/or a rule from cybermalveillance.gouv.fr), which scam tricks it
uses (urgency, fake authority, too-good reward, fear) and one simple sentence explaining why,
something a grandparent can understand. A local LLM (Qwen) writes the answer after calling my
own tool `check_sms`, and a guard in code blocks any answer that invents a trick or repeats a
link or phone number from the scam.

## Model

Qwen3.5-4B, quantized Q4_K_M (file `Qwen3.5-4B-Q4_K_M.gguf`, 2.7 GB, not in the repo),
served locally by llama.cpp's `llama-server` with an OpenAI-compatible API at
`http://localhost:8080/v1`. Thinking mode is turned off in every call.

Download: https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/blob/main/Qwen3.5-4B-Q4_K_M.gguf
(Unsloth's GGUF of the official model https://huggingface.co/Qwen/Qwen3.5-4B).
SHA256: `00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4`

```bash
llama-server -m path/to/Qwen3.5-4B-Q4_K_M.gguf --port 8080 -c 8192 --jinja -ngl 99 --device Vulkan1'''

and the note: "On my laptop (Vulkan build of llama.cpp) the NVIDIA GPU is Vulkan1; run llama-server --list-devices and use yours (e.g. CUDA0 on a CUDA build). Without --device, llama.cpp may split the model onto a weak integrated GPU and become very slow." Also add `python -m tools.tactics_eval` to the "Other scripts" line
`

## Setup and run

Requires **Python 3.11+**. From the project folder:

```bash
python -m venv .venv
.venv\Scripts\activate              # Linux/WSL: source .venv/bin/activate
pip install -r requirements.txt
python data/download.py             # SMS data -> data/raw/
python data/clean.py                # -> data/train.csv, data/test.csv, data/cleaning_log.md
python model/train.py               # -> model/classifier.pkl, model/report.md
python -m pytest tests              # tests (no llama-server needed)
streamlit run app.py                # demo page (llama-server must be running), Ctrl+C to stop
```

Expected: download.py saves 5,574 rows, clean.py keeps 5,160 (4,128 train / 1,032 test), and
model/report.md shows threshold 0.11 with F1 0.863. Different numbers mean the data is different.

Other scripts (llama-server must be running), see EVIDENCE.md:
`python -m agent.loop`, `python judge/qwen_judge.py`, `python -m bench.run`.

Careful: `python judge/qwen_judge.py` rewrites judge/scores.csv and judge/report.md, and
`python -m bench.run` rewrites bench/results.md and the traces in traces/bench/, so the numbers in
EVIDENCE.md would no longer match. To test the benchmark without touching the evidence, use
`python -m bench.run --quick` (3 tasks, 1 run, traces in traces/bench_quick/).

## Credits

- Data: SMS Spam Collection, T. A. Almeida and J. M. Gómez Hidalgo (2011),
  "Contributions to the Study of SMS Spam Filtering: New Collection and Results",
  UCI Machine Learning Repository (id 228), licence CC BY 4.0.
  Mirror used if UCI fails: github.com/justmarkham/pycon-2016-tutorial.
- Rule "no serious company asks for bank details or a password by message":
  Cybermalveillance.gouv.fr, leaflet "L'hameçonnage",
  https://www.cybermalveillance.gouv.fr/medias/2026/02/260129_FicheReflexe_Hameconnage.pdf
