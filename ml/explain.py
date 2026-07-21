import os
import joblib
import shap
import pandas as pd

_model = None
_explainer = None


def _get_latest_model_path() -> str:
    """Finds the highest-versioned model folder under ml/models/, so this
    file never needs manual updates when a new model version is trained."""
    models_dir = "ml/models"
    versions = [
        d for d in os.listdir(models_dir)
        if os.path.isdir(os.path.join(models_dir, d)) and d.startswith("v")
    ]
    if not versions:
        raise FileNotFoundError(f"No model versions found in {models_dir}")
    versions.sort(key=lambda v: [int(x) for x in v.lstrip("v").split(".")])
    latest = versions[-1]
    return os.path.join(models_dir, latest, "model.pkl")


def _load_model():
    global _model, _explainer
    if _model is None:
        _model = joblib.load(_get_latest_model_path())
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
    if feat_name == "has_obfuscated_ip":
        return "URL hides an IP address using decimal or hex encoding — a known evasion technique" if value == 1 else None
    if feat_name == "has_non_ascii":
        return "URL contains non-standard characters that visually mimic a real domain (homograph attack)" if value == 1 else None
    if feat_name == "brand_similarity_flag":
        return "Domain closely resembles a well-known brand name — possible typosquat" if value == 1 else None
    if feat_name == "brand_in_subdomain_flag":
        return "A known brand name appears as a fake subdomain while the real domain is unrelated" if value == 1 else None
    if feat_name == "has_suspicious_tld":
        return "Domain uses a free/disposable TLD commonly abused for phishing" if value == 1 else None
    if feat_name == "suspicious_keyword_count":
        return f"URL contains {int(value)} phishing-associated keywords (e.g. 'secure', 'verify', 'login')" if value > 0 else None
    return f"{feat_name} contributed to this score"
        
def explain_prediction(feature_row: dict, top_n: int = 3) -> dict:
    model, explainer = _load_model()

    X = pd.DataFrame([feature_row]).drop(columns=["has_https", "suspicious_keyword_count"], errors="ignore")
    proba = model.predict_proba(X)[0][1]
    score = round(proba * 100)

    # Rule-based override: these signals are rare in training data but
    # near-deterministic indicators of phishing, so the ML model alone
    # can't be trusted to weight them correctly. Force a high floor.
    override_reason = None
    if feature_row.get("has_obfuscated_ip") == 1:
        score = max(score, 90)
        override_reason = "URL hides an IP address using decimal or hex encoding — a known evasion technique"
    elif feature_row.get("has_non_ascii") == 1:
        score = max(score, 90)
        override_reason = "URL contains non-standard characters that visually mimic a real domain (homograph attack)"
    elif feature_row.get("brand_in_subdomain_flag") == 1:
        score = max(score, 90)
        override_reason = "A known brand name appears as a fake subdomain while the real domain is unrelated — a common impersonation trick"
    elif feature_row.get("brand_similarity_flag") == 1:
        score = min(100, score + 35)  # partial boost, not a hard floor — this signal can have false positives
    elif feature_row.get("has_suspicious_tld") == 1:
        score = min(100, score + 30)  # strong signal — legitimate major services rarely use these TLDs

    # Suspicious keyword density gets a small nudge regardless of other
    # overrides — real login pages exist too, so this must stay gentle.
    kw_count = feature_row.get("suspicious_keyword_count", 0)
    if kw_count >= 3:
        score = min(100, score + 10)

    shap_values = explainer.shap_values(X)
    values = shap_values[0]
    feature_names = X.columns.tolist()

    contributions = list(zip(feature_names, values))
    contributions.sort(key=lambda x: abs(x[1]), reverse=True)

    reasons = []
    if override_reason:
        reasons.append(override_reason)
    for feat_name, impact in contributions:
        if impact > 0:  # pushed toward "phishing"
            actual_value = feature_row[feat_name]
            description = _describe_feature(feat_name, actual_value)
            if description and description not in reasons:  # skip duplicates and non-supporting features
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