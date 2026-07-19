import pandas as pd

df = pd.read_csv("data/raw/phishing_urls.csv", on_bad_lines="skip")

print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nLabel counts:")
print(df["Label"].value_counts())
print("\nSample rows:")
print(df.head())