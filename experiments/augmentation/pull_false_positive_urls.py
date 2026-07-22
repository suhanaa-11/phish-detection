import pandas as pd
from sklearn.model_selection import train_test_split
import joblib

ORIGINAL_DATASET_SIZE = 549346

print("Loading augmented features + model...")
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

false_positives_original = results[
    (results["true_label"] == 0) &
    (results["pred_label"] == 1) &
    (results.index < ORIGINAL_DATASET_SIZE)
]

print(f"False positives from original dataset: {len(false_positives_original)}")

print("Loading raw URLs to map indices back to actual URL text...")
raw = pd.read_csv("data/raw/phishing_urls.csv", on_bad_lines="skip")
raw = raw.dropna(subset=["URL", "Label"]).reset_index(drop=True)

# raw's positional order matches features.csv's row order (both built via
# raw["URL"].tolist() in build_dataset.py, so position i in each aligns)
sample = false_positives_original.head(30)
print(f"\n--- Sample of {len(sample)} false-positive URLs (from {len(false_positives_original)} total) ---")
for idx, row in sample.iterrows():
    url = raw.iloc[idx]["URL"]
    label = raw.iloc[idx]["Label"]
    print(f"  [{idx}] label={label:5} url={url}")