import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.explain import explain_prediction
from ml.features.pipeline import build_feature_row


def test_ip_based_url_flagged_as_risky():
    features = build_feature_row("http://192.168.1.1/login-verify.php?id=1")
    result = explain_prediction(features)
    assert result["score"] >= 50
    assert result["verdict"] == "phishing"
    assert len(result["top_reasons"]) > 0


def test_clean_https_url_scores_lower():
    features = build_feature_row("https://www.wikipedia.org")
    result = explain_prediction(features)
    assert "score" in result
    assert "verdict" in result


def test_explanation_returns_readable_reasons():
    features = build_feature_row("http://192.168.1.1/login-verify.php?id=1")
    result = explain_prediction(features)
    for reason in result["top_reasons"]:
        assert isinstance(reason, str)
        assert len(reason) > 0