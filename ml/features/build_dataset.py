import pandas as pd
from ml.features.pipeline import build_feature_dataframe

print("Loading raw data...")
raw = pd.read_csv("data/raw/phishing_urls.csv", on_bad_lines="skip")
raw = raw.dropna(subset=["URL", "Label"])

print(f"Total rows: {len(raw)}")
print("Extracting lexical features (this may take a few minutes for 549k rows)...")

features_df = build_feature_dataframe(raw["URL"].tolist(), include_domain_features=False)
features_df["label"] = raw["Label"].values

print("Saving to data/processed/features.csv...")
import os
os.makedirs("data/processed", exist_ok=True)
features_df.to_csv("data/processed/features.csv", index=False)

print("Done. Shape:", features_df.shape)
print(features_df.head())