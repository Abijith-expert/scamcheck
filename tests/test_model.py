from model.train import predict_proba

# needs model/train.py to have been run first (it creates model/classifier.pkl)


def test_obvious_spam_is_above_half():
    assert predict_proba("WINNER! Claim your free prize now, call 09061234567") > 0.5


def test_normal_message_is_below_half():
    assert predict_proba("See you at lunch tomorrow?") < 0.5
