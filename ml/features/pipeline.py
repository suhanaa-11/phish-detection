import pandas as pd
from ml.features.lexical import extract_lexical_features
from ml.features.domain import extract_domain_features


def build_feature_row(url: str, include_domain_features: bool = False) -> dict:
    features = extract_lexical_features(url)
    if include_domain_features:
        features.update(extract_domain_features(url))
    return features


def build_feature_dataframe(urls: list, include_domain_features: bool = False) -> pd.DataFrame:
    rows = [build_feature_row(url, include_domain_features) for url in urls]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    sample_urls = [
        "https://www.google.com",
        "http://192.168.1.1/login-verify.php?id=39284",
    ]
    df = build_feature_dataframe(sample_urls)
    print(df)