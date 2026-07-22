import pandas as pd
from urllib.parse import urlparse

print("Loading raw dataset...")
raw = pd.read_csv("data/raw/phishing_urls.csv", on_bad_lines="skip")
raw = raw.dropna(subset=["URL", "Label"])

def path_depth(url: str) -> int:
    try:
        u = url if "//" in url else "http://" + url
        path = urlparse(u).path
        segments = [s for s in path.split("/") if s]
        return len(segments)
    except Exception:
        # Malformed URL (e.g. stray brackets breaking IPv6 parsing) —
        # fall back to a naive slash count instead of failing the whole run
        return url.count("/")
    
raw["path_depth"] = raw["URL"].astype(str).map(path_depth)

good = raw[raw["Label"] == "good"]["path_depth"]
bad = raw[raw["Label"] == "bad"]["path_depth"]

print(f"\nGood URLs (n={len(good)}):")
print(f"  Mean path depth: {good.mean():.2f}")
print(f"  % with 0 path segments (bare domain): {(good == 0).mean()*100:.1f}%")
print(f"  % with 2+ path segments: {(good >= 2).mean()*100:.1f}%")

print(f"\nBad URLs (n={len(bad)}):")
print(f"  Mean path depth: {bad.mean():.2f}")
print(f"  % with 0 path segments (bare domain): {(bad == 0).mean()*100:.1f}%")
print(f"  % with 2+ path segments: {(bad >= 2).mean()*100:.1f}%")