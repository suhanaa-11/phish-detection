import joblib
import shap
import pandas as pd

_model = None
_explainer = None

FEATURE_LABELS = {
    "url_length": "URL is unusually long",
    "entropy": "URL contains unusually random/obfuscated characters",
    "digit_count": "URL contains many digits",
    "special_char_count": "URL has many special characters (@, -, %, =, &)",
    "has_ip": "URL uses a raw IP address instead of a domain name",
    "subdomain_count": "URL has an unusual number of subdomains",
    "has_https": "URL does not use HTTPS",
}


def _load_model():
    global _model, _explainer
    if _model is None:
        _model = joblib.load("ml/models/v0.1.0/model.pkl")
        _explainer = shap.TreeExplainer(_model)
    return _model, _explainer


def explain_prediction(feature_row: dict, top_n: int = 3) -> dict:
    """
    Takes a single feature dict (from ml/features/pipeline.py),
    returns a risk score (0-100) and top human-readable reasons.
    """
    model, explainer = _load_model()

    X = pd.DataFrame([feature_row])
    proba = model.predict_proba(X)[0][1]  # probability of "bad"
    score = round(proba * 100)

    shap_values = explainer.shap_values(X)
    # shap_values shape: (1, n_features) for binary XGBoost
    values = shap_values[0]
    feature_names = X.columns.tolist()

    # Pair each feature with its SHAP contribution, sort by absolute impact
    contributions = list(zip(feature_names, values))
    contributions.sort(key=lambda x: abs(x[1]), reverse=True)

    reasons = []
    for feat_name, impact in contributions[:top_n]:
        if impact > 0:  # pushed toward "phishing"
            reasons.append(FEATURE_LABELS.get(feat_name, feat_name))

    return {
        "score": score,
        "verdict": "phishing" if score >= 50 else "likely safe",
        "top_reasons": reasons,
    }


if __name__ == "__main__":
    from ml.features.pipeline import build_feature_row

    test_url = "http://192.168.1.1/login-verify-account.php?user=admin&id=39284"
    features = build_feature_row(test_url)
    result = explain_prediction(features)
    print(f"URL: {test_url}")
    print(result)