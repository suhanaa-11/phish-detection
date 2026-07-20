import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.url_extractor import extract_urls_from_text


def test_extracts_multiple_urls():
    text = "Visit http://example.com/login and also www.test-site.com/verify"
    urls = extract_urls_from_text(text)
    assert len(urls) == 2


def test_deduplicates_urls():
    text = "Go to http://example.com twice: http://example.com again"
    urls = extract_urls_from_text(text)
    assert len(urls) == 1


def test_strips_trailing_punctuation():
    text = "Check this out: http://example.com/page."
    urls = extract_urls_from_text(text)
    assert urls[0] == "http://example.com/page"


def test_empty_text_returns_empty_list():
    assert extract_urls_from_text("") == []


def test_no_urls_in_plain_text():
    text = "This is just a normal sentence with no links."
    assert extract_urls_from_text(text) == []