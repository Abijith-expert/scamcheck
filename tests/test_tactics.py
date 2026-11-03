from tools.check_sms import check_sms
from tools.tactics import asks_for_sensitive, detect_links, detect_tactics


def test_urgency():
    assert detect_tactics("Reply NOW to keep your offer") == ["urgency"]


def test_fake_authority():
    assert detect_tactics("Message from Ameli about your file") == ["fake_authority"]


def test_reward():
    assert detect_tactics("Congratulations, you are a WINNER") == ["reward"]


def test_fear():
    assert detect_tactics("Votre dossier est bloqué") == ["fear"]


def test_several_tricks():
    text = "URGENT: your bank account is suspended"
    assert detect_tactics(text) == ["urgency", "fake_authority", "fear"]


def test_normal_message_has_no_trick():
    assert detect_tactics("See you at lunch tomorrow?") == []


def test_whole_words_only():
    # "know" contains "now" and "Snowden" contains "now": must not count as urgency
    assert detect_tactics("I know, I watched Snowden") == []


def test_links_and_phone_numbers():
    text = "Call 09061209465 or go to www.example.com/win"
    assert detect_links(text) == ["www.example.com/win", "09061209465"]


def test_sensitive_with_link():
    assert asks_for_sensitive("Enter your card number here: http://example.com/pay")


def test_sensitive_in_french():
    assert asks_for_sensitive("Colissimo : payer 1,99€ sur https://colis-suivi.fr")


def test_sensitive_word_without_link_is_false():
    assert not asks_for_sensitive("I forgot my PIN, can you call me?")


def test_link_without_sensitive_word_is_false():
    assert not asks_for_sensitive("Photos from the party: https://example.com/album")


def test_rule_forces_scam_verdict():
    # the classifier alone says safe (0.016 < threshold 0.11), the rule makes it a scam
    result = check_sms("Hi mum, I lost my phone, can you send your card details on https://example.com/help")
    assert result["scam_probability"] < 0.11
    assert result["asks_for_sensitive"] is True
    assert result["is_scam"] is True
