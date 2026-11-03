from agent.guard import check_reply
from agent.loop import fallback

RESULT = {"is_scam": True, "scam_probability": 0.9, "tactics": ["urgency"],
          "links": ["09061234567"], "asks_for_sensitive": False}

GOOD_REPLY = ("Verdict: scam\nFlagged by: urgency\n"
              "Why: It pushes you to act fast so you do not have time to think.")


def test_invented_trick_is_blocked():
    ok, reasons = check_reply("Verdict: scam\nFlagged by: urgency, fear", RESULT)
    assert not ok
    assert "fear" in reasons[0]


def test_invented_trick_in_french_is_blocked():
    ok, _ = check_reply("Verdict: scam\nCe message joue sur la peur.", RESULT)
    assert not ok


def test_short_link_is_blocked():
    ok, reasons = check_reply(GOOD_REPLY + " Do not open bit.ly/abc", RESULT)
    assert not ok
    assert reasons == ["contains a link"]


def test_phone_number_is_blocked():
    ok, reasons = check_reply(GOOD_REPLY + " Do not call 0612345678.", RESULT)
    assert not ok
    assert reasons == ["contains a phone number"]


def test_correct_reply_passes():
    assert check_reply(GOOD_REPLY, RESULT) == (True, [])


def test_no_tool_call_is_blocked():
    ok, _ = check_reply(GOOD_REPLY, None)
    assert not ok


def test_fallback_always_passes_the_guard():
    assert check_reply(fallback(RESULT), RESULT) == (True, [])
