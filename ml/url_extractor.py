import re

URL_PATTERN = re.compile(
    r'(?:(?:https?|ftp)://|www\.)[^\s<>"\']+', re.IGNORECASE
)


def extract_urls_from_text(text: str) -> list:
    """Finds all URL-like substrings in a block of text (e.g. pasted email content)."""
    matches = URL_PATTERN.findall(text)
    # de-duplicate while preserving order
    seen = set()
    unique = []
    for url in matches:
        cleaned = url.rstrip('.,;:!?)')  # trim trailing punctuation often stuck to URLs in text
        if cleaned not in seen:
            seen.add(cleaned)
            unique.append(cleaned)
    return unique


if __name__ == "__main__":
    sample_text = """
    Dear user, please verify your account at http://192.168.1.1/login-verify.php?id=1.
    Also check www.paypa1-secure.com/account for details. Visit https://legit-bank.com/help.
    """
    print(extract_urls_from_text(sample_text))