import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
import joblib

print("Loading original features.csv (not the augmented version)...")
df = pd.read_csv("data/processed/features.csv")

X = df.drop(columns=["label", "has_https", "suspicious_keyword_count"])
y = df["label"].map({"bad": 1, "good": 0})

# Same split params as the original v0.7.0 training/tuning, so this is an
# apples-to-apples measurement of the actual production model's behavior
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Loading v0.7.0 (production) model...")
model = joblib.load("ml/models/v0.7.0/model.pkl")

y_pred = model.predict(X_test)

print("\n--- v0.7.0 on original dataset test split ---")
print(classification_report(y_test, y_pred, target_names=["good", "bad"]))

cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:")
print(cm)

tn, fp, fn, tp = cm.ravel()
good_total = tn + fp
print(f"\nTotal 'good' URLs in test set: {good_total}")
print(f"Correctly classified as safe (true negatives): {tn}")
print(f"Incorrectly flagged as phishing (false positives): {fp}")
print(f"False positive rate on legitimate URLs: {fp / good_total * 100:.2f}%")