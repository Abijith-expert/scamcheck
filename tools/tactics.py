"""Simple keyword rules to spot scam tricks, links and requests for sensitive data."""
import re

# one small word list per trick, English and French, matched as whole words
TACTICS = {
    "urgency": ["urgent", "now", "today", "24h", "last chance", "maintenant"],
    "fake_authority": ["bank", "account", "police", "ameli", "caf", "colissimo", "compte"],
    "reward": ["won", "winner", "free", "prize", "claim", "gagné", "gratuit"],
    "fear": ["blocked", "suspended", "fine", "legal", "bloqué", "suspendu", "amende"],
}

URL_PATTERN = r"(?:https?://|www\.)\S+"
PHONE_PATTERN = r"\+?\d[\d -]{7,}\d"  # at least 9 digits, spaces or dashes allowed

SENSITIVE_WORDS = ["bank details", "card", "password", "pin", "code", "pay", "payment",
                   "rib", "mot de passe", "carte", "payer", "paiement"]


def has_word(text, word):
    """True if word appears in text as a whole word, ignoring case."""
    return re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE) is not None


def detect_tactics(text):
    """List of the trick names found in the text, e.g. ["urgency", "reward"]."""
    found = []
    for name, words in TACTICS.items():
        if any(has_word(text, word) for word in words):
            found.append(name)
    return found


def detect_links(text):
    """All URLs and phone numbers in the text."""
    return re.findall(URL_PATTERN, text) + re.findall(PHONE_PATTERN, text)


def asks_for_sensitive(text):
    """Rule from cybermalveillance.gouv.fr, see "Rule not in the file" in data/cleaning_log.md:
    no serious company asks for bank details, a password or a payment by message.
    True if the text has a sensitive word AND a link."""
    has_sensitive_word = any(has_word(text, word) for word in SENSITIVE_WORDS)
    has_link = re.search(URL_PATTERN, text) is not None
    return has_sensitive_word and has_link
