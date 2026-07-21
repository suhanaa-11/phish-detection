import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import roc_auc_score, classification_report
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

scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

param_dist = {
    "n_estimators": [200, 300, 400, 500],
    "max_depth": [4, 5, 6, 7, 8],
    "learning_rate": [0.03, 0.05, 0.1, 0.15],
    "subsample": [0.7, 0.8, 0.9, 1.0],
    "colsample_bytree": [0.7, 0.8, 0.9, 1.0],
    "min_child_weight": [1, 3, 5],
}

base_model = XGBClassifier(
    scale_pos_weight=scale_pos_weight,
    eval_metric="logloss",
    random_state=42,
)

print("Running randomized search (this will take several minutes)...")
search = RandomizedSearchCV(
    base_model,
    param_distributions=param_dist,
    n_iter=25,
    scoring="roc_auc",
    cv=3,
    verbose=2,
    random_state=42,
    n_jobs=-1,
)
search.fit(X_train, y_train)

print("\nBest params:", search.best_params_)
print("Best CV ROC-AUC:", search.best_score_)

best_model = search.best_estimator_
y_pred = best_model.predict(X_test)
y_proba = best_model.predict_proba(X_test)[:, 1]

print("\n--- Classification Report (tuned model on held-out test set) ---")
print(classification_report(y_test, y_pred, target_names=["good", "bad"]))
print("ROC-AUC:", roc_auc_score(y_test, y_proba))

os.makedirs("ml/models/v0.7.0", exist_ok=True)
joblib.dump(best_model, "ml/models/v0.7.0/model.pkl")
print("\nModel saved to ml/models/v0.7.0/model.pkl")