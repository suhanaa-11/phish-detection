import pandas as pd
from sklearn.model_selection import train_test_split
import joblib

ORIGINAL_DATASET_SIZE = 549346  # rows before the augmented additions were appended

print("Loading augmented dataset and model...")
df = pd.read_csv("data/processed/features_augmented.csv")
model = joblib.load("ml/models/augmented_experiment/model.pkl")

X = df.drop(columns=["label", "has_https", "suspicious_keyword_count"])
y = df["label"].map({"bad": 1, "good": 0})

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

y_pred = model.predict(X_test)

results = X_test.copy()
results["true_label"] = y_test.values
results["pred_label"] = y_pred
results["source"] = ["augmented" if idx >= ORIGINAL_DATASET_SIZE else "original" for idx in X_test.index]

false_positives = results[(results["true_label"] == 0) & (results["pred_label"] == 1)]
true_negatives = results[(results["true_label"] == 0) & (results["pred_label"] == 0)]

print(f"\nTotal false positives (good URLs predicted as phishing): {len(false_positives)}")
print(f"  From original dataset:  {(false_positives['source'] == 'original').sum()}")
print(f"  From our augmented URLs: {(false_positives['source'] == 'augmented').sum()}")

print(f"\nFor reference — total 'good' test rows by source:")
print(results[results['true_label'] == 0]['source'].value_counts())

print("\n--- Mean feature values: false positives vs correctly-classified good URLs ---")
feature_cols = [c for c in X.columns]
comparison = pd.DataFrame({
    "false_positives_mean": false_positives[feature_cols].mean(),
    "true_negatives_mean": true_negatives[feature_cols].mean(),
})
comparison["difference"] = comparison["false_positives_mean"] - comparison["true_negatives_mean"]
print(comparison.sort_values("difference", key=abs, ascending=False))

print("\n--- Sample of 10 false-positive rows (feature values) ---")
print(false_positives[feature_cols].head(10).to_string())