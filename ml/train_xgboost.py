import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from xgboost import XGBClassifier
import joblib
import os

print("Loading processed features...")
df = pd.read_csv("data/processed/features.csv")

X = df.drop(columns=["label", "has_https", "suspicious_keyword_count"])
y = df["label"].map({"bad": 1, "good": 0})

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Training XGBoost...")
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    scale_pos_weight=scale_pos_weight,
    eval_metric="logloss",
    random_state=42,
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print("\n--- Classification Report ---")
print(classification_report(y_test, y_pred, target_names=["good", "bad"]))
print("ROC-AUC:", roc_auc_score(y_test, y_proba))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

os.makedirs("ml/models/v0.6.0", exist_ok=True)
joblib.dump(model, "ml/models/v0.6.0/model.pkl")
print("\nModel saved to ml/models/v0.6.0/model.pkl")