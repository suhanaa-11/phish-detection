import random
import pandas as pd
from tranco import Tranco
from ml.features.pipeline import build_feature_dataframe

N_DOMAINS = 100000
RANDOM_SEED = 42

# Realistic mix of shapes real URLs take — deliberately varied so the
# augmented rows don't collapse into one narrow, artificial feature-space
# cluster the way bare "domain.com"-only rows did last time.
URL_TEMPLATES = [
    "{domain}",
    "http://{domain}",
    "https://{domain}",
    "https://www.{domain}",
    "https://www.{domain}/",
    "https://{domain}/login",
    "https://www.{domain}/about-us",
    "https://{domain}/search?q=example",
    "https://www.{domain}/account/settings",
    "http://www.{domain}/index.html",
    "https://www.{domain}/blog/how-to-get-started",
    "https://{domain}/products/item-4521",
    "https://www.{domain}/track?utm_source=newsletter&utm_medium=email",
    "https://{domain}/user/12345/profile",
    "https://www.{domain}/checkout?order_id=98213&ref=cart",
    "https://{domain}/articles/2024-annual-report",
]


def build_realistic_url(domain: str, rng: random.Random) -> str:
    template = rng.choice(URL_TEMPLATES)
    return template.format(domain=domain)


print(f"Fetching Tranco top {N_DOMAINS} domains (cached locally after first run)...")
t = Tranco(cache=True, cache_dir=".tranco_cache")
latest_list = t.list()
popular_domains = latest_list.top(N_DOMAINS)
print(f"Got {len(popular_domains)} domains. Example: {popular_domains[:5]}")

print("Loading raw URLs to check for overlap (URL-level dedup, not feature-level)...")
raw = pd.read_csv("data/raw/phishing_urls.csv", on_bad_lines="skip")
raw = raw.dropna(subset=["URL", "Label"])

def normalize(url: str) -> str:
    u = url.strip().lower()
    u = u.replace("https://", "").replace("http://", "")
    if u.startswith("www."):
        u = u[4:]
    return u.rstrip("/")

existing_normalized = set(raw["URL"].astype(str).map(normalize))

before_count = len(popular_domains)
popular_domains = [d for d in popular_domains if normalize(d) not in existing_normalized]
overlap = before_count - len(popular_domains)
print(f"Filtered {overlap} domains already present in the raw dataset; {len(popular_domains)} new domains remain.")

print("Generating varied realistic URL shapes for each domain...")
rng = random.Random(RANDOM_SEED)
popular_urls = [build_realistic_url(d, rng) for d in popular_domains]
print("Example generated URLs:", popular_urls[:8])

print("Extracting lexical features for the new popular-domain URLs...")
popular_df = build_feature_dataframe(popular_urls, include_domain_features=False)
popular_df["label"] = "good"

print("Loading existing features.csv...")
existing_df = pd.read_csv("data/processed/features.csv")

before_good = (existing_df["label"] == "good").sum()
before_bad = (existing_df["label"] == "bad").sum()

augmented_df = pd.concat([existing_df, popular_df], ignore_index=True)

after_good = (augmented_df["label"] == "good").sum()
after_bad = (augmented_df["label"] == "bad").sum()

print(f"\nBefore: good={before_good}, bad={before_bad}, total={len(existing_df)}")
print(f"After:  good={after_good}, bad={after_bad}, total={len(augmented_df)}")
print(f"Rows added: {len(augmented_df) - len(existing_df)} (expected: {len(popular_domains)})")

augmented_df.to_csv("data/processed/features_augmented.csv", index=False)
print("\nSaved to data/processed/features_augmented.csv")