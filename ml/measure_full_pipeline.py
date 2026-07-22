import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
import joblib

print("Loading original features.csv + v0.7.0 model...")
df = pd.read_csv("data/processed/features.csv")

# Split the FULL dataframe (not just model-input X) so we retain access to
# has_suspicious_tld, brand_similarity_flag, etc. for applying the same
# override logic that's live in ml/explain.py — not just the raw model.
train_df, test_df = train_test_split(
    df, test_size=0.2, random_state=42, stratify=df["label"]
)

model = joblib.load("ml/models/v0.7.0/model.pkl")

X_test = test_df.drop(columns=["label", "has_https", "suspicious_keyword_count"])
y_test = test_df["label"].map({"bad": 1, "good": 0})

proba = model.predict_proba(X_test)[:, 1]
raw_scores = (proba * 100).round().astype(int)

final_scores = []
for i, (_, row) in enumerate(test_df.iterrows()):
    score = raw_scores[i]
    if row.get("has_obfuscated_ip") == 1:
        score = max(score, 90)
    elif row.get("has_non_ascii") == 1:
        score = max(score, 90)
    elif row.get("brand_in_subdomain_flag") == 1:
        score = max(score, 90)
    elif row.get("brand_similarity_flag") == 1:
        score = min(100, score + 50)
    elif row.get("has_suspicious_tld") == 1:
        score = min(100, score + 30)

    if row.get("suspicious_keyword_count", 0) >= 3:
        score = min(100, score + 10)

    final_scores.append(score)

final_scores = pd.Series(final_scores, index=test_df.index)
y_pred_final = (final_scores >= 60).astype(int)

# For comparison: raw model only, same 0.60 threshold, no overrides
y_pred_raw_only = (raw_scores >= 60).astype(int)

def report(name, y_pred):
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    good_total = tn + fp
    bad_total = fn + tp
    fp_rate = fp / good_total * 100
    recall = tp / bad_total * 100
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
    print(f"\n--- {name} ---")
    print(f"FP rate (good flagged as phishing): {fp_rate:.2f}%")
    print(f"Recall (phishing caught):           {recall:.2f}%")
    print(f"Precision (phishing flags correct): {precision:.2f}%")

report("Raw model only, threshold 0.60", y_pred_raw_only)
report("Full pipeline: threshold 0.60 + rule overrides", y_pred_final)