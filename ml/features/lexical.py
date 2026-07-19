import re
import math
from urllib.parse import urlparse


def get_url_length(url: str) -> int:
    return len(url)


def get_entropy(url: str) -> float:
    """Shannon entropy — random-looking/obfuscated URLs tend to score higher."""
    if not url:
        return 0.0
    prob = [url.count(c) / len(url) for c in set(url)]
    return -sum(p * math.log2(p) for p in prob)


def count_digits(url: str) -> int:
    return sum(c.isdigit() for c in url)


def count_special_chars(url: str) -> int:
    return len(re.findall(r"[@\-_%=&?]", url))


def has_ip_address(url: str) -> int:
    """1 if the host looks like a raw IP address instead of a domain name."""
    pattern = r"(\d{1,3}\.){3}\d{1,3}"
    return 1 if re.search(pattern, url) else 0


def count_subdomains(url: str) -> int:
    try:
        netloc = urlparse(url if "://" in url else "http://" + url).netloc
        parts = netloc.split(".")
        return max(0, len(parts) - 2)
    except Exception:
        return 0


def has_https(url: str) -> int:
    return 1 if url.strip().lower().startswith("https") else 0


def extract_lexical_features(url: str) -> dict:
    return {
        "url_length": get_url_length(url),
        "entropy": get_entropy(url),
        "digit_count": count_digits(url),
        "special_char_count": count_special_chars(url),
        "has_ip": has_ip_address(url),
        "subdomain_count": count_subdomains(url),
        "has_https": has_https(url),
    }


if __name__ == "__main__":
    test_url = "http://192.168.1.1/login-verify-account.php?user=admin&id=39284"
    print(extract_lexical_features(test_url))