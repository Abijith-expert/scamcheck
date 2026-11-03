"""check_sms(text): the tool Qwen calls. Combines the classifier and the rules."""
from pathlib import Path

import joblib

from tools.tactics import asks_for_sensitive, detect_links, detect_tactics

MODEL_FILE = Path(__file__).parent.parent / "model" / "classifier.pkl"


def check_sms(text):
    saved = joblib.load(MODEL_FILE)  # {"model": ..., "threshold": ...} from model/train.py
    probability = float(saved["model"].predict_proba([text])[0][1])
    sensitive = asks_for_sensitive(text)

    # rule from data/cleaning_log.md ("Rule not in the file"):
    # asking for bank details / password / payment through a link = scam,
    # whatever the classifier says
    flagged_by_classifier = probability >= saved["threshold"]
    is_scam = flagged_by_classifier or sensitive

    return {
        "is_scam": bool(is_scam),
        "scam_probability": round(probability, 3),
        "flagged_by_classifier": bool(flagged_by_classifier),
        "tactics": detect_tactics(text),
        "links": detect_links(text),
        "asks_for_sensitive": sensitive,
    }
