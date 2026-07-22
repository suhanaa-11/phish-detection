import joblib
import pandas as pd
from scipy.sparse import hstack, csr_matrix
from ml.features.pipeline import build_feature_row

print("Loading TF-IDF experiment model + vectorizer...")
model = joblib.load("ml/models/tfidf_experiment/model.pkl")
vectorizer = joblib.load("ml/models/tfidf_experiment/vectorizer.pkl")

tests = [
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

correct = 0
for url, expected in tests:
    lexical_features = build_feature_row(url)
    lexical_row = pd.DataFrame([lexical_features]).drop(
        columns=["has_https", "suspicious_keyword_count"], errors="ignore"
    )

    tfidf_vec = vectorizer.transform([url])
    combined = hstack([tfidf_vec, csr_matrix(lexical_row.values)])

    proba = model.predict_proba(combined)[0][1]
    score = round(proba * 100)
    got = "phishing" if score >= 50 else "safe"
    mark = "OK" if got == expected else "MISS"
    if got == expected:
        correct += 1
    print(f"{mark:4} {url[:55]:55} expected={expected:9} got={got:9} score={score}")

print(f"\n{correct}/{len(tests)} correct")