import pandas as pd
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
proba = model.predict_proba(X_test)[:, 1]

print(f"\n{'Threshold':>10} {'FP rate (good)':>16} {'Recall (bad)':>14} {'Precision (bad)':>17}")
for threshold in [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
    y_pred = (proba >= threshold).astype(int)

    good_mask = (y_test == 0)
    bad_mask = (y_test == 1)

    fp_rate = ((y_pred == 1) & good_mask).sum() / good_mask.sum()
    recall = ((y_pred == 1) & bad_mask).sum() / bad_mask.sum()
    predicted_bad = (y_pred == 1).sum()
    precision = ((y_pred == 1) & bad_mask).sum() / predicted_bad if predicted_bad > 0 else 0

    print(f"{threshold:>10.2f} {fp_rate*100:>15.2f}% {recall*100:>13.2f}% {precision*100:>16.2f}%")