import pandas as pd
import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from xgboost import XGBClassifier

print("Loading raw URLs...")
raw = pd.read_csv("data/raw/phishing_urls.csv", on_bad_lines="skip")
raw = raw.dropna(subset=["URL", "Label"])

print("Loading existing lexical features...")
lexical = pd.read_csv("data/processed/features.csv")

assert len(raw) == len(lexical), (
    f"Row count mismatch: raw={len(raw)} vs lexical={len(lexical)} — "
    "rebuild data/processed/features.csv first with the current build_dataset.py"
)

y = lexical["label"].map({"bad": 1, "good": 0})
lexical_X = lexical.drop(columns=["label", "has_https", "suspicious_keyword_count"])

print("Building TF-IDF character n-gram features...")
vectorizer = TfidfVectorizer(
    analyzer="char",
    ngram_range=(3, 5),
    max_features=3000,
    min_df=5,
)
tfidf_X = vectorizer.fit_transform(raw["URL"].astype(str))
print("TF-IDF shape:", tfidf_X.shape)

print("Combining TF-IDF + lexical features...")
combined_X = hstack([tfidf_X, csr_matrix(lexical_X.values)])
print("Combined shape:", combined_X.shape)

X_train, X_test, y_train, y_test = train_test_split(
    combined_X, y, test_size=0.2, random_state=42, stratify=y
)

scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

print("Training XGBoost on combined feature set...")
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

print("\n--- Classification Report (TF-IDF + lexical combined) ---")
print(classification_report(y_test, y_pred, target_names=["good", "bad"]))
print("ROC-AUC:", roc_auc_score(y_test, y_proba))
print("\n(Compare against v0.7.0 baseline: ROC-AUC 0.869, accuracy 0.80)")

import joblib
import os

os.makedirs("ml/models/tfidf_experiment", exist_ok=True)
joblib.dump(model, "ml/models/tfidf_experiment/model.pkl")
joblib.dump(vectorizer, "ml/models/tfidf_experiment/vectorizer.pkl")
print("\nSaved experiment model + vectorizer to ml/models/tfidf_experiment/")