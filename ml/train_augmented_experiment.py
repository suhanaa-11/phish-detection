import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from xgboost import XGBClassifier
import joblib
import os

print("Loading augmented features...")
df = pd.read_csv("data/processed/features_augmented.csv")

X = df.drop(columns=["label", "has_https", "suspicious_keyword_count"])
y = df["label"].map({"bad": 1, "good": 0})

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Training XGBoost on augmented dataset (using v0.7.0's tuned hyperparameters)...")
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

model = XGBClassifier(
    n_estimators=500,
    max_depth=7,
    learning_rate=0.15,
    subsample=0.7,
    colsample_bytree=1.0,
    min_child_weight=3,
    scale_pos_weight=scale_pos_weight,
    eval_metric="logloss",
    random_state=42,
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print("\n--- Classification Report (augmented experiment) ---")
print(classification_report(y_test, y_pred, target_names=["good", "bad"]))
print("ROC-AUC:", roc_auc_score(y_test, y_proba))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

os.makedirs("ml/models/augmented_experiment", exist_ok=True)
joblib.dump(model, "ml/models/augmented_experiment/model.pkl")
print("\nModel saved to ml/models/augmented_experiment/model.pkl (NOT auto-loaded by explain.py — safe experiment)")