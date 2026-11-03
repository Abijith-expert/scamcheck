"""Agent loop: Qwen gets an SMS, calls check_sms, answers, and the guard checks
the answer in code. Every run is saved as JSON in traces/.

Run from the project folder: python -m agent.loop
"""
import os

# Must run BEFORE numpy / scikit-learn are imported: with llama-server using most of the RAM,
# OpenBLAS starting one thread per CPU core can crash with "Memory allocation still failed".
# One thread is enough here. setdefault keeps any value already set in the terminal.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from openai import OpenAI

from agent.guard import check_reply
from tools.check_sms import check_sms

ROOT = Path(__file__).parent.parent
MAX_ROUNDS = 3
NO_THINKING = {"chat_template_kwargs": {"enable_thinking": False}}

# llama-server does not check the key, but the client needs one
client = OpenAI(base_url="http://localhost:8080/v1", api_key="none")

SYSTEM_PROMPT = """You check SMS messages for scams, for elderly people.
Always call the check_sms tool first, with the full SMS.
Then answer in exactly this format:
Verdict: scam or safe (scam if is_scam is true in the tool result)
Flagged by: the tactics from the tool, plus "asks for bank details or a password" if asks_for_sensitive is true, or nothing
Why: ONE simple sentence a grandparent would understand
Do not give the probability as a number.
Never repeat any link or phone number from the SMS."""

# check_sms described in the OpenAI tools format
TOOLS = [{
    "type": "function",
    "function": {
        "name": "check_sms",
        "description": "Checks an SMS: scam probability from a trained classifier, scam tricks, links and phone numbers.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "The full SMS to check"}},
            "required": ["text"],
        },
    },
}]


def now():
    return datetime.now().isoformat(timespec="seconds")


def fallback(tool_result):
    """Safe answer built only from the tool result, used when the guard blocks Qwen twice."""
    if tool_result is None:
        return ("Verdict: unknown\nFlagged by: nothing\n"
                "Why: I could not check this message, so do not click or call anything in it.")
    flagged = list(tool_result["tactics"])
    if tool_result["asks_for_sensitive"]:
        flagged.append("asks for bank details or a password")
    if tool_result["is_scam"]:
        verdict, why = "scam", "This message looks like a scam, so do not answer it, click or call anything in it."
    else:
        verdict, why = "safe", "Nothing in this message looks like a scam."
    return f"Verdict: {verdict}\nFlagged by: {', '.join(flagged) or 'nothing'}\nWhy: {why}"


def run(sms, temperature=0.7, trace_dir=ROOT / "traces", trace_name=None):
    """Run the loop on one SMS and return the trace (a dict with "final_answer", "tool_calls",
    "guard", ...). The trace is saved as JSON in trace_dir, or not saved if trace_dir is None."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": sms}]
    trace = {"started": now(), "sms": sms, "tool_calls": [], "guard": [], "final_answer": None}
    answer = None

    for round_number in range(1, MAX_ROUNDS + 1):
        response = client.chat.completions.create(
            model="qwen", messages=messages, tools=TOOLS, temperature=temperature,
            extra_body=NO_THINKING)
        reply = response.choices[0].message

        # no tool call means this is the final answer: stop
        if not reply.tool_calls:
            answer = reply.content
            messages.append({"role": "assistant", "content": answer})
            break

        # the model asked for a tool: run it and send the result back
        messages.append(reply.model_dump(exclude_none=True))
        for call in reply.tool_calls:
            arguments = json.loads(call.function.arguments)
            if call.function.name == "check_sms":
                result = check_sms(arguments["text"])
            else:
                result = {"error": f"unknown tool {call.function.name}"}
            trace["tool_calls"].append({"round": round_number, "time": now(),
                                        "tool": call.function.name,
                                        "arguments": arguments, "result": result})
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": json.dumps(result)})

    # guard, in code: check the answer against the last check_sms result
    tool_result = trace["tool_calls"][-1]["result"] if trace["tool_calls"] else None
    ok, reasons = check_reply(answer, tool_result)
    trace["guard"].append({"time": now(), "reply": answer, "ok": ok, "reasons": reasons})

    # blocked: ask the model once more and tell it why (no tools this time)
    if not ok and tool_result is not None:
        messages.append({"role": "user", "content": "Your answer was blocked because it "
                         + "; ".join(reasons) + ". Write it again and follow the rules."})
        response = client.chat.completions.create(
            model="qwen", messages=messages, temperature=temperature, extra_body=NO_THINKING)
        answer = response.choices[0].message.content
        messages.append({"role": "assistant", "content": answer})
        ok, reasons = check_reply(answer, tool_result)
        trace["guard"].append({"time": now(), "reply": answer, "ok": ok, "reasons": reasons})

    # still blocked: safe answer built only from the tool result
    if not ok:
        answer = fallback(tool_result)
        trace["guard"].append({"time": now(), "fallback_used": True})

    trace["final_answer"] = answer
    trace["messages"] = messages
    trace["finished"] = now()
    if trace_dir is not None:
        trace_dir.mkdir(parents=True, exist_ok=True)
        file = trace_dir / f"{trace_name or f'{datetime.now():%Y%m%d-%H%M%S-%f}'}.json"
        file.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Trace saved to {file}")
    return trace


if __name__ == "__main__":
    # only messages from the dataset, never real personal SMS
    test = pd.read_csv(ROOT / "data" / "test.csv")
    examples = test.groupby("label").sample(1, random_state=42)["message"]  # 1 ham + 1 spam
    for sms in examples:
        print("SMS:", sms)
        print(run(sms)["final_answer"])
        print()
