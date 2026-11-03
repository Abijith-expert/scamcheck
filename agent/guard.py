"""Guard: checks Qwen's final reply IN CODE before the user sees it."""
import re

from tools.tactics import PHONE_PATTERN, URL_PATTERN, has_word

# the words that NAME each trick, English and French
TRICK_NAMES = {
    "urgency": ["urgency", "urgence"],
    "fake_authority": ["fake authority", "fake_authority", "fausse autorité"],
    "reward": ["reward", "récompense"],
    "fear": ["fear", "peur"],
}

# links with http:// or www., plus short ones like bit.ly/abc or example.com
LINK_PATTERN = URL_PATTERN + r"|\b[\w-]+\.[a-z]{2,}\b"


def check_reply(reply, tool_result):
    """Return (ok, reasons). ok is False if the reply must be blocked."""
    if not reply:
        return False, ["empty reply"]
    if tool_result is None:
        return False, ["check_sms was not called"]

    reasons = []

    # (a) the reply names a trick that check_sms did not detect
    for trick, names in TRICK_NAMES.items():
        if trick not in tool_result["tactics"] and any(has_word(reply, n) for n in names):
            reasons.append(f"names the trick '{trick}' but check_sms did not detect it")

    # (b) the reply contains a link or a phone number
    if re.search(LINK_PATTERN, reply):
        reasons.append("contains a link")
    if re.search(PHONE_PATTERN, reply):
        reasons.append("contains a phone number")

    return len(reasons) == 0, reasons
