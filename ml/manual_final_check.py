from ml.features.pipeline import build_feature_row
from ml.explain import explain_prediction

# Deliberately NOT reusing the 14 cases from test_regression_suite.py --
# this is an independent spot-check with fresh URLs before deployment.

REAL_URLS = [
    "https://www.amazon.com/gp/css/order-history",
    "https://en.wikipedia.org/wiki/Machine_learning",
    "https://github.com/torvalds/linux",
    "https://www.nytimes.com/section/technology",
    "https://docs.python.org/3/library/os.html",
    "https://www.irs.gov/forms-instructions",
    "https://stackoverflow.com/questions/tagged/python",
    "https://www.linkedin.com/in/satyanadella",
    "https://www.who.int/health-topics/coronavirus",
    "https://mail.google.com/mail/u/0/#inbox",
]

FAKE_URLS = [
    "http://secure-paypal-verification.com/login",
    "http://192.168.10.5/wp-admin/verify.php",
    "https://www.microsft-support.com/reset-password",
    "http://bit-ly-secure-login.tk/account",
    "https://appleid-verify.apple.com.security-check.ru",
    "http://xn--80ak6aa92e.com/login",
    "https://www.amaz0n-rewards.com/claim",
    "http://3232235521/bank-login",
    "https://google.com.verify-account.info/",
    "http://update-your-billing-info-now.xyz/secure",
]

def run(label, urls, expected):
    print(f"\n=== {label} ===")
    correct = 0
    for url in urls:
        feature_row = build_feature_row(url)
        result = explain_prediction(feature_row)
        score = result["score"]
        verdict = result["verdict"]
        got_safe = verdict == "likely safe"
        is_correct = got_safe if expected == "safe" else not got_safe
        mark = "OK" if is_correct else "MISS"
        if is_correct:
            correct += 1
        reasons = "; ".join(r for r in result.get("top_reasons", [])[:2])
        print(f"{mark:4} score={score:3} verdict={verdict:11} {url[:55]:55}")
        if reasons:
            print(f"       reasons: {reasons}")
    print(f"\n{label}: {correct}/{len(urls)} correct")
    return correct

r1 = run("Real/legitimate URLs (expect: safe)", REAL_URLS, "safe")
r2 = run("Fake/phishing URLs (expect: phishing)", FAKE_URLS, "phishing")

print(f"\n=== TOTAL: {r1 + r2}/{len(REAL_URLS) + len(FAKE_URLS)} correct ===")