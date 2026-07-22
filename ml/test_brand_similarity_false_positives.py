from ml.test_regression_suite import score_url
import joblib

CANDIDATES = [
    "https://amzn.to",
    "https://instagr.am",
    "https://www.abode.com",
]

for model_path in ["ml/models/v0.7.0/model.pkl", "ml/models/augmented_experiment/model.pkl"]:
    print(f"\n=== {model_path} ===")
    model = joblib.load(model_path)
    for url in CANDIDATES:
        score = score_url(model, url)
        verdict = "phishing" if score >= 50 else "safe"
        print(f"  {url:30} score={score:4} verdict={verdict}")