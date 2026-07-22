import pandas as pd
from ml.features.domain import extract_domain_features

print("Loading raw dataset...")
raw = pd.read_csv("data/raw/phishing_urls.csv", on_bad_lines="skip")
raw = raw.dropna(subset=["URL", "Label"])

SAMPLE_SIZE = 300  # small, fast, enough to see if there's a real signal

good_sample = raw[raw["Label"] == "good"].sample(n=SAMPLE_SIZE, random_state=42)
bad_sample = raw[raw["Label"] == "bad"].sample(n=SAMPLE_SIZE, random_state=42)

def get_ages(df, label):
    ages = []
    failed = 0
    for i, url in enumerate(df["URL"]):
        result = extract_domain_features(url)
        if result["domain_lookup_failed"] == 1:
            failed += 1
        else:
            ages.append(result["domain_age_days"])
        if (i + 1) % 50 == 0:
            print(f"  {label}: {i+1}/{len(df)} done...")
    return ages, failed

print(f"\nLooking up domain ages for {SAMPLE_SIZE} 'good' URLs...")
good_ages, good_failed = get_ages(good_sample, "good")

print(f"\nLooking up domain ages for {SAMPLE_SIZE} 'bad' URLs...")
bad_ages, bad_failed = get_ages(bad_sample, "bad")

print(f"\n--- Results ---")
print(f"Good: {len(good_ages)}/{SAMPLE_SIZE} successful lookups, {good_failed} failed")
if good_ages:
    print(f"  Mean age: {sum(good_ages)/len(good_ages):.0f} days ({sum(good_ages)/len(good_ages)/365:.1f} years)")
    print(f"  Median age: {sorted(good_ages)[len(good_ages)//2]} days")

print(f"\nBad: {len(bad_ages)}/{SAMPLE_SIZE} successful lookups, {bad_failed} failed")
if bad_ages:
    print(f"  Mean age: {sum(bad_ages)/len(bad_ages):.0f} days ({sum(bad_ages)/len(bad_ages)/365:.1f} years)")
    print(f"  Median age: {sorted(bad_ages)[len(bad_ages)//2]} days")