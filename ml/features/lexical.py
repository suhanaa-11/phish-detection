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

def has_obfuscated_ip(url: str) -> int:
    """1 if hostname is an IP address encoded as decimal, hex, or octal
    instead of standard dotted-decimal notation (a common evasion trick)."""
    try:
        netloc = urlparse(url if "://" in url else "http://" + url).netloc
        host = netloc.split("@")[-1].split(":")[0]

        if host.isdigit():
            return 1 if 0 <= int(host) <= 4294967295 else 0

        hex_pattern = r"^0x[0-9a-fA-F]{1,2}(\.0x[0-9a-fA-F]{1,2}){3}$"
        if re.match(hex_pattern, host):
            return 1

        if re.match(r"^0x[0-9a-fA-F]{6,8}$", host):
            return 1

        return 0
    except Exception:
        return 0


def has_non_ascii(url: str) -> int:
    """1 if the hostname contains non-ASCII characters (e.g. Cyrillic
    look-alikes used in IDN homograph attacks)."""
    try:
        netloc = urlparse(url if "://" in url else "http://" + url).netloc
        host = netloc.split("@")[-1].split(":")[0]
        return 1 if any(ord(c) > 127 for c in host) else 0
    except Exception:
        return 0


KNOWN_BRANDS = [
    "paypal", "google", "apple", "amazon", "microsoft", "facebook",
    "netflix", "instagram", "twitter", "linkedin", "ebay", "chase",
    "wellsfargo", "bankofamerica", "dropbox", "adobe",
]


def _edit_distance(a: str, b: str) -> int:
    """Standard Levenshtein distance, no external dependency."""
    if len(a) < len(b):
        a, b = b, a
    prev_row = range(len(b) + 1)
    for i, ca in enumerate(a, 1):
        curr_row = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr_row.append(min(
                prev_row[j] + 1,
                curr_row[j - 1] + 1,
                prev_row[j - 1] + cost
            ))
        prev_row = curr_row
    return prev_row[-1]

def _normalize_homoglyphs(text: str) -> str:
    """Collapse common visual substitutions used in typosquats before
    comparing against real brand names."""
    replacements = [
        ("rn", "m"), ("vv", "w"), ("0", "o"),
        ("1", "l"), ("5", "s"), ("3", "e"), ("@", "a"),
    ]
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    return result

def brand_similarity_flag(url: str) -> int:
    """1 if hostname is suspiciously close (edit distance 1-2) to a known
    brand name without being an exact match — classic typosquat signal."""
    try:
        netloc = urlparse(url if "://" in url else "http://" + url).netloc
        host = netloc.split("@")[-1].split(":")[0].lower()
        label = re.split(r"[.\-]", host)[0]
        normalized_label = _normalize_homoglyphs(label)

        for brand in KNOWN_BRANDS:
            if label == brand:
                continue
            dist = min(
                _edit_distance(label, brand),
                _edit_distance(normalized_label, brand),
            )
            if dist <= 2 and len(label) >= len(brand) - 2:
                return 1
        return 0
    except Exception:
        return 0

def extract_lexical_features(url: str) -> dict:
    return {
        "url_length": get_url_length(url),
        "entropy": get_entropy(url),
        "digit_count": count_digits(url),
        "special_char_count": count_special_chars(url),
        "has_ip": has_ip_address(url),
        "subdomain_count": count_subdomains(url),
        "has_https": has_https(url),
        "has_obfuscated_ip": has_obfuscated_ip(url),
        "has_non_ascii": has_non_ascii(url),
        "brand_similarity_flag": brand_similarity_flag(url),
        "brand_in_subdomain_flag": brand_in_subdomain_flag(url),
    }

def brand_in_subdomain_flag(url: str) -> int:
    """1 if a known brand name appears as a non-final label in the hostname
    while the actual registered domain is something else entirely —
    catches 'paypal.com.evil-domain.xyz' style impersonation."""
    try:
        netloc = urlparse(url if "://" in url else "http://" + url).netloc
        host = netloc.split("@")[-1].split(":")[0].lower()
        labels = host.split(".")

        if len(labels) < 3:
            return 0

        registered_domain = labels[-2]  # e.g. "verify-account-security-check" in the .xyz example
        earlier_labels = labels[:-2]    # everything before the real registered domain

        for brand in KNOWN_BRANDS:
            if registered_domain == brand:
                continue  # it's actually the brand's real domain, not impersonation
            if brand in earlier_labels:
                return 1
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    test_url = "http://192.168.1.1/login-verify-account.php?user=admin&id=39284"
    print(extract_lexical_features(test_url))