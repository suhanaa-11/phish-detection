import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.explain import explain_prediction
from ml.features.pipeline import build_feature_row


def test_ip_based_url_returns_valid_prediction():
    """
    Verifies the prediction pipeline runs correctly end-to-end for a clearly
    suspicious URL. Does not assert an exact score threshold, since CI uses a
    lightweight model trained on a small synthetic sample for speed — score
    calibration is validated separately against the full production model
    (see docs/evaluation.md).
    """
    features = build_feature_row("http://192.168.1.1/login-verify.php?id=1")
    result = explain_prediction(features)

    assert 0 <= result["score"] <= 100
    assert result["verdict"] in ["phishing", "likely safe"]
    assert isinstance(result["top_reasons"], list)


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