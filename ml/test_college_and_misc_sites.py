from ml.features.pipeline import build_feature_row
from ml.explain import explain_prediction

REAL_SITES = [
    ("SSIPMT Raipur (main domain)", "https://ssipmt.edu.in/"),
    ("SSIPMT Raipur (alt domain, .com)", "https://www.ssipmt.com/"),
    ("SSIPMT contact page", "https://ssipmt.edu.in/contact.php"),
    ("CSVTU official site", "https://csvtu.ac.in/"),
    ("CSVTU 'about' page", "https://csvtu.ac.in/ew/the-university/overview/"),
    ("Google", "https://www.google.com"),
    ("Wikipedia", "https://en.wikipedia.org/wiki/India"),
    ("GitHub repo", "https://github.com/pytorch/pytorch"),
    ("Amazon India", "https://www.amazon.in/gp/help/customer/display.html"),
    ("Indian Railways (IRCTC)", "https://www.irctc.co.in/nget/train-search"),
]

FAKE_SITES = [
    ("Fake college portal typosquat", "http://ssipmt-student-portal-login.tk/verify"),
    ("Fake university result page", "http://csvtu-result-update.info/login.php"),
    ("Fake bank alert", "http://secure-sbi-verification.com/update-kyc"),
    ("Fake IRCTC refund scam", "http://irctc-refund-claim.xyz/form"),
    ("Fake govt scholarship scam", "http://scholarship-govt-in.tk/apply-now"),
]

def run(label, sites, expected):
    print(f"\n=== {label} ===")
    correct = 0
    for name, url in sites:
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
        print(f"{mark:4} score={score:3} verdict={verdict:11} [{name}]")
        print(f"       {url}")
        if reasons:
            print(f"       reasons: {reasons}")
    print(f"\n{label}: {correct}/{len(sites)} correct")
    return correct

r1 = run("Real college/university/misc sites (expect: safe)", REAL_SITES, "safe")
r2 = run("Fake/phishing-style sites (expect: phishing)", FAKE_SITES, "phishing")
print(f"\n=== TOTAL: {r1 + r2}/{len(REAL_SITES) + len(FAKE_SITES)} correct ===")