import joblib
import shap
import pandas as pd
from ml.features.pipeline import build_feature_row

print("Loading augmented_experiment model...")
model = joblib.load("ml/models/augmented_experiment/model.pkl")
explainer = shap.TreeExplainer(model)

urls_to_check = [
    "https://stackoverflow.com",
    "https://www.google.com/accounts/login",
    "https://www.wikipedia.org",
]

for url in urls_to_check:
    feature_row = build_feature_row(url)
    X = pd.DataFrame([feature_row]).drop(columns=["has_https", "suspicious_keyword_count"], errors="ignore")
    proba = model.predict_proba(X)[0][1]
    score = round(proba * 100)

    shap_values = explainer.shap_values(X)[0]
    contributions = sorted(zip(X.columns.tolist(), shap_values), key=lambda x: abs(x[1]), reverse=True)

    print(f"\n=== {url} (score={score}) ===")
    for feat, val in contributions:
        direction = "toward PHISHING" if val > 0 else "toward safe"
        print(f"  {feat:25} shap={val:+.3f}  ({direction})  actual_value={feature_row[feat]}")