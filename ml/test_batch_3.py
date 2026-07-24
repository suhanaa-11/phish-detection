from ml.features.pipeline import build_feature_row
from ml.explain import explain_prediction

REAL_SITES = [
    ("Flipkart", "https://www.flipkart.com/electronics/mobiles/pr?sid=tyy%2C4io"),
    ("Times of India", "https://timesofindia.indiatimes.com/india"),
    ("Income Tax India e-filing", "https://www.incometax.gov.in/iec/foportal/"),
    ("Zomato", "https://www.zomato.com/raipur"),
    ("LinkedIn Jobs", "https://www.linkedin.com/jobs/search/?keywords=software%20engineer"),
    ("NPTEL (IIT online courses)", "https://nptel.ac.in/courses"),
]

FAKE_SITES = [
    ("Fake crypto giveaway", "http://elon-musk-btc-giveaway.tk/claim-now"),
    ("Fake WhatsApp gift scam", "http://whatsapp-gift-2025.xyz/redeem?id=48213"),
    ("Fake job offer scam", "http://hdfc-bank-job-vacancy-apply.info/register"),
    ("Fake income tax refund", "http://incometax-refund-status-check.tk/verify"),
    ("Fake OTP/UPI scam", "http://paytm-cashback-claim-now.ml/upi-verify"),
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

r1 = run("Real sites (expect: safe)", REAL_SITES, "safe")
r2 = run("Fake/scam sites (expect: phishing)", FAKE_SITES, "phishing")
print(f"\n=== TOTAL: {r1 + r2}/{len(REAL_SITES) + len(FAKE_SITES)} correct ===")