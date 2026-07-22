import pandas as pd
import shap
from sklearn.model_selection import train_test_split
import joblib

print("Loading original features.csv + v0.7.0 model...")
df = pd.read_csv("data/processed/features.csv")

X = df.drop(columns=["label", "has_https", "suspicious_keyword_count"])
y = df["label"].map({"bad": 1, "good": 0})

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = joblib.load("ml/models/v0.7.0/model.pkl")
y_pred = model.predict(X_test)

results = X_test.copy()
results["true_label"] = y_test.values
results["pred_label"] = y_pred

false_positives = results[(results["true_label"] == 0) & (results["pred_label"] == 1)]
true_negatives = results[(results["true_label"] == 0) & (results["pred_label"] == 0)]

print(f"Total false positives: {len(false_positives)}")
print(f"Total true negatives: {len(true_negatives)}")

# Sample for SHAP (TreeExplainer on the full 13k+ FPs would be slow; a
# representative sample is enough to see the dominant pattern)
SAMPLE_SIZE = 1000
fp_sample = false_positives.sample(n=min(SAMPLE_SIZE, len(false_positives)), random_state=42)
tn_sample = true_negatives.sample(n=min(SAMPLE_SIZE, len(true_negatives)), random_state=42)

feature_cols = X.columns.tolist()

print(f"\nRunning SHAP on {len(fp_sample)} false positives and {len(tn_sample)} true negatives...")
explainer = shap.TreeExplainer(model)

fp_shap = explainer.shap_values(fp_sample[feature_cols])
tn_shap = explainer.shap_values(tn_sample[feature_cols])

fp_mean_shap = pd.Series(fp_shap.mean(axis=0), index=feature_cols)
tn_mean_shap = pd.Series(tn_shap.mean(axis=0), index=feature_cols)

comparison = pd.DataFrame({
    "fp_mean_shap": fp_mean_shap,
    "tn_mean_shap": tn_mean_shap,
    "difference": fp_mean_shap - tn_mean_shap,
}).sort_values("difference", key=abs, ascending=False)

print("\n--- Mean SHAP contribution: false positives vs true negatives ---")
print("(positive = pushes toward 'phishing'; negative = pushes toward 'safe')")
print(comparison)

print("\n--- Feature value comparison (means) ---")
value_comparison = pd.DataFrame({
    "fp_mean_value": fp_sample[feature_cols].mean(),
    "tn_mean_value": tn_sample[feature_cols].mean(),
})
print(value_comparison)