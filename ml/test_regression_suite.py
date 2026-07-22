import argparse
import joblib
import pandas as pd
from ml.features.pipeline import build_feature_row

TESTS = [
    ("https://www.google.com/accounts/login", "safe"),
    ("https://www.microsoft.com", "safe"),
    ("https://www.reddit.com", "safe"),
    ("https://stackoverflow.com", "safe"),
    ("https://www.paypal.com", "safe"),
    ("https://www.wikipedia.org", "safe"),
    ("https://www.facebook.com", "safe"),
    ("http://secure-login-verify-account-update.tk", "phishing"),
    ("http://faceb00k-account-recovery-help.net", "phishing"),
    ("http://appleid.apple.com.secure-verify-now.info", "phishing"),
    ("http://arnaz0n-orders.com", "phishing"),
    ("https://www.аpple.com", "phishing"),
    ("http://3627734018/login-verify", "phishing"),
    ("http://paypa1-security-alert.com", "phishing"),
]


def score_url(model, url: str) -> int:
    """Replicates explain.py's scoring path: raw model proba + the same
    rule-based override layer, so this suite reflects real production
    behavior, not just raw model output."""
    feature_row = build_feature_row(url)
    X = pd.DataFrame([feature_row]).drop(columns=["has_https", "suspicious_keyword_count"], errors="ignore")
    proba = model.predict_proba(X)[0][1]
    score = round(proba * 100)

    if feature_row.get("has_obfuscated_ip") == 1:
        score = max(score, 90)
    elif feature_row.get("has_non_ascii") == 1:
        score = max(score, 90)
    elif feature_row.get("brand_in_subdomain_flag") == 1:
        score = max(score, 90)
    elif feature_row.get("brand_similarity_flag") == 1:
        score = min(100, score + 50)
    elif feature_row.get("has_suspicious_tld") == 1:
        score = min(100, score + 30)

    kw_count = feature_row.get("suspicious_keyword_count", 0)
    if kw_count >= 3:
        score = min(100, score + 10)

    return score


def run_suite(model_path: str):
    print(f"Loading model from {model_path}...")
    model = joblib.load(model_path)

    correct = 0
    for url, expected in TESTS:
        score = score_url(model, url)
        got = "phishing" if score >= 60 else "safe"
        mark = "OK" if got == expected else "MISS"
        if got == expected:
            correct += 1
        print(f"{mark:4} {url[:55]:55} expected={expected:9} got={got:9} score={score}")

    print(f"\n{correct}/{len(TESTS)} correct")
    return correct


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True, help="Path to model.pkl to test")
    args = parser.parse_args()
    run_suite(args.model_path)
    