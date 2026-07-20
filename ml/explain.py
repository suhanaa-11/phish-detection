import joblib
import shap
import pandas as pd

_model = None
_explainer = None


def _load_model():
    global _model, _explainer
    if _model is None:
        _model = joblib.load("ml/models/v0.2.0/model.pkl")
        _explainer = shap.TreeExplainer(_model)
    return _model, _explainer


def _describe_feature(feat_name: str, value) -> str:
    """Generate a human-readable reason based on the ACTUAL feature value."""
    if feat_name == "url_length":
        return f"URL is unusually long ({int(value)} characters)"
    if feat_name == "entropy":
        return f"URL contains unusually random/obfuscated characters (entropy {value:.2f})"
    if feat_name == "digit_count":
        return f"URL contains many digits ({int(value)})"
    if feat_name == "special_char_count":
        return f"URL has several special characters ({int(value)} found)" if value > 0 else None
    if feat_name == "has_ip":
        return "URL uses a raw IP address instead of a domain name" if value == 1 else None
    if feat_name == "subdomain_count":
        return f"URL has an unusual number of subdomains ({int(value)})"
    return f"{feat_name} contributed to this score"
        
def explain_prediction(feature_row: dict, top_n: int = 3) -> dict:
    model, explainer = _load_model()

    X = pd.DataFrame([feature_row]).drop(columns=["has_https"], errors="ignore")
    proba = model.predict_proba(X)[0][1]
    score = round(proba * 100)

    shap_values = explainer.shap_values(X)
    values = shap_values[0]
    feature_names = X.columns.tolist()

    contributions = list(zip(feature_names, values))
    contributions.sort(key=lambda x: abs(x[1]), reverse=True)

    reasons = []
    for feat_name, impact in contributions:
        if impact > 0:  # pushed toward "phishing"
            actual_value = feature_row[feat_name]
            description = _describe_feature(feat_name, actual_value)
            if description:  # skip features where the value doesn't actually support the direction
                reasons.append(description)
        if len(reasons) >= top_n:
            break

    return {
        "score": score,
        "verdict": "phishing" if score >= 50 else "likely safe",
        "top_reasons": reasons,
    }


if __name__ == "__main__":
    from ml.features.pipeline import build_feature_row

    for test_url in [
        "http://192.168.1.1/login-verify-account.php?user=admin&id=39284",
        "https://www.wikipedia.org",
    ]:
        features = build_feature_row(test_url)
        result = explain_prediction(features)
        print(f"\nURL: {test_url}")
        print(result)