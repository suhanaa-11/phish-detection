import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.features.lexical import extract_lexical_features


def test_has_ip_detects_ip_address():
    features = extract_lexical_features("http://192.168.1.1/login")
    assert features["has_ip"] == 1


def test_has_ip_false_for_normal_domain():
    features = extract_lexical_features("https://www.google.com")
    assert features["has_ip"] == 0


def test_has_https_true():
    features = extract_lexical_features("https://example.com")
    assert features["has_https"] == 1


def test_has_https_false():
    features = extract_lexical_features("http://example.com")
    assert features["has_https"] == 0


def test_url_length():
    url = "http://abc.com"
    features = extract_lexical_features(url)
    assert features["url_length"] == len(url)


def test_subdomain_count():
    features = extract_lexical_features("http://mail.login.example.com")
    assert features["subdomain_count"] == 2