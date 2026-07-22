import joblib
import shap
import pandas as pd
from ml.features.pipeline import build_feature_row

url = "http://faceb00k-account-recovery-help.net"
feature_row = build_feature_row(url)

print(f"=== Raw feature values for {url} ===")
for k, v in feature_row.items():
    print(f"  {k:25} = {v}")

for model_path in ["ml/models/v0.7.0/model.pkl", "ml/models/augmented_experiment/model.pkl"]:
    print(f"\n=== {model_path} ===")
    model = joblib.load(model_path)
    explainer = shap.TreeExplainer(model)

    X = pd.DataFrame([feature_row]).drop(columns=["has_https", "suspicious_keyword_count"], errors="ignore")
    proba = model.predict_proba(X)[0][1]
    raw_score = round(proba * 100)
    print(f"  Raw model score (before overrides): {raw_score}")

    # Check which override rules would/wouldn't fire
    print(f"  has_obfuscated_ip={feature_row.get('has_obfuscated_ip')}, "
          f"has_non_ascii={feature_row.get('has_non_ascii')}, "
          f"brand_in_subdomain_flag={feature_row.get('brand_in_subdomain_flag')}, "
          f"brand_similarity_flag={feature_row.get('brand_similarity_flag')}, "
          f"has_suspicious_tld={feature_row.get('has_suspicious_tld')}, "
          f"suspicious_keyword_count={feature_row.get('suspicious_keyword_count')}")

    shap_values = explainer.shap_values(X)[0]
    contributions = sorted(zip(X.columns.tolist(), shap_values), key=lambda x: abs(x[1]), reverse=True)
    print("  SHAP contributions:")
    for feat, val in contributions:
        direction = "toward PHISHING" if val > 0 else "toward safe"
        print(f"    {feat:25} shap={val:+.3f}  ({direction})  actual_value={feature_row[feat]}")