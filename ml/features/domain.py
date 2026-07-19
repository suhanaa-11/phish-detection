import whois
from datetime import datetime


def get_domain_age_days(url: str) -> int:
    """Returns domain age in days, or -1 if lookup fails or data is unavailable."""
    try:
        host = url.split("//")[-1].split("/")[0]
        w = whois.whois(host)
        creation_date = w.creation_date

        if isinstance(creation_date, list):
            creation_date = creation_date[0] if creation_date else None

        if not isinstance(creation_date, datetime):
            return -1

        age = (datetime.now() - creation_date).days
        return max(age, 0)
    except Exception:
        return -1


def extract_domain_features(url: str) -> dict:
    age = get_domain_age_days(url)
    return {
        "domain_age_days": age,
        "domain_lookup_failed": 1 if age == -1 else 0,
    }


if __name__ == "__main__":
    print(extract_domain_features("https://www.google.com"))