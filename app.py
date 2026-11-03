"""ScamCheck demo page. Run with: streamlit run app.py (llama-server must be running).
Nothing pasted here is saved: the agent loop runs with trace_dir=None."""
import os

# Must run BEFORE numpy / scikit-learn are imported: with llama-server using most of the RAM,
# OpenBLAS starting one thread per CPU core can crash with "Memory allocation still failed".
# One thread is enough here. setdefault keeps any value already set in the terminal.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import re

import streamlit as st

from agent.loop import run

EXAMPLES = {
    "Spam example": "URGENT! We are trying to contact U. Todays draw shows that you have won a "
                    "£2000 prize GUARANTEED. Call 09058094507 from land line. Claim 3030. Valid 12hrs only",
    "Normal example": "Is that what time you want me to come?",
    "French scam": "Colissimo : votre colis est bloqué. Vous devez payer 1,99 € maintenant "
                   "pour la livraison : https://colissimo-suivi.example/payer",
}

st.set_page_config(page_title="ScamCheck")
st.title("ScamCheck")
st.write("Paste a text message (SMS) and find out if it is a scam.")

# example buttons: they fill the text box
for column, (label, text) in zip(st.columns(3), EXAMPLES.items()):
    if column.button(label):
        st.session_state["sms"] = text

sms = st.text_area("Paste an SMS", key="sms", height=120)

if st.button("Check", type="primary") and sms.strip():
    try:
        with st.spinner("Checking..."):
            trace = run(sms, trace_dir=None)  # trace_dir=None: nothing is saved
    except Exception:
        st.error("Could not reach the model. Is llama-server running?")
        st.stop()

    answer = trace["final_answer"] or ""
    result = trace["tool_calls"][-1]["result"] if trace["tool_calls"] else None
    verdict = re.search(r"verdict:\s*(scam|safe)", answer, re.IGNORECASE)
    why = re.search(r"why:\s*(.+)", answer, re.IGNORECASE)

    # 1. big verdict
    if verdict and verdict.group(1).lower() == "scam":
        st.error("# SCAM")
    elif verdict:
        st.success("# SAFE")
    else:
        st.warning("# NOT SURE")

    # 2. what flagged it, tricks as small tags, explanation
    if result is not None:
        flags = []
        if result["flagged_by_classifier"]:
            flags.append("the classifier")
        if result["asks_for_sensitive"]:
            flags.append("the bank-details rule")
        if flags:
            st.write("Flagged by " + " and ".join(flags))
        if result["tactics"]:
            st.markdown("Tricks found: " + " ".join(f"`{tag}`" for tag in result["tactics"]))
    if why:
        st.write(why.group(1))

    # 3. note if the guard blocked an answer
    if any(not step.get("ok", True) for step in trace["guard"]):
        if any(step.get("fallback_used") for step in trace["guard"]):
            st.caption("Note: the safety check blocked the model's answers, "
                       "so this answer was built directly from the checks.")
        else:
            st.caption("Note: the safety check blocked a first answer, the model rewrote it.")
