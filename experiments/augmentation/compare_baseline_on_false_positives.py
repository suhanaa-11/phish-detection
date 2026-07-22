import joblib
from ml.test_regression_suite import score_url

# The 30 sampled false-positive URLs from the augmented model, pulled from
# the original dataset (paste the exact URL column values here)
sample_urls = [
    "www.cs.arizona.edu/patterns/weaving/books/ctw_chem_2.pdf",
    "wn.com/Toon_Disney",
    "springpulsepoetryfestival.com/03-drummond.htm",
    "linkedin.com/in/marionadon",
    "pipl.com/directory/people/William/DePriest",
    "charlestonwineandfood.com/personalities/charleston-chefs/",
    "astore.amazon.com/lewisblackstore-20",
    "southafricab2b.co.za/odp/index.cgi?show=/Business/Food_and_Related_Products/Confectionery/",
    "email.utah.gov/",
    "askbiography.com/bio/Trevor_Plouffe.html",
    "nctc.net/hazard/conrad/shadoe/",
    "utoronto.ca/dcb-dbc/dcba/listOfSubjects/m.htm",
    "www.hastingsresearch.com/whitepapers/taunting.shtml",
    "tvnz.co.nz/hunger/show-2301232",
    "www.globalhemp.com/Archives/Essays/Fiber/fiber_wars.html",
    "oregonyouthsoccer.org/",
    "www.angelfire.com/games2/pantheon/",
    "findmapping.com/toronto-montreal/highway401.php",
    "whitehouse.gov/about/presidents/",
    "jewishgen.org/Belarus/newsletter/Vysotsky.htm",
    "linkedin.com/directory/people/taitz.html",
    "eu33.com/records-Adams/",
    "rentals.com/Arkansas/Trumann/",
    "catholicity.com/churchteaching/",
    "bullfrogpower.com/09releases/astral.cfm",
    "steinbachmbchurch.org/resources.shtml",
    "www.swcp.com/~walt/fortran_store/Html/Info/books/f90.html",
    "reverbnation.com/killa1nce",
    "linkedin.com/in/jennmacleanangus",
    "westincrowncenterkansascity.com/",
]

v070_model = joblib.load("ml/models/v0.7.0/model.pkl")
augmented_model = joblib.load("ml/models/augmented_experiment/model.pkl")

v070_wrong = 0
augmented_wrong = 0
both_wrong = 0

print(f"{'URL':65} {'v0.7.0':>10} {'augmented':>10}")
for url in sample_urls:
    s1 = score_url(v070_model, url)
    s2 = score_url(augmented_model, url)
    v1_wrong = s1 >= 50
    v2_wrong = s2 >= 50
    if v1_wrong:
        v070_wrong += 1
    if v2_wrong:
        augmented_wrong += 1
    if v1_wrong and v2_wrong:
        both_wrong += 1
    flag = "  <-- both wrong" if v1_wrong and v2_wrong else ("  <-- only augmented" if v2_wrong and not v1_wrong else "")
    print(f"{url[:65]:65} {s1:>10} {s2:>10}{flag}")

print(f"\nv0.7.0 flags as phishing:    {v070_wrong}/{len(sample_urls)}")
print(f"augmented flags as phishing: {augmented_wrong}/{len(sample_urls)}")
print(f"Both wrong (pre-existing weakness): {both_wrong}/{len(sample_urls)}")
print(f"Only augmented wrong (new regression): {augmented_wrong - both_wrong}/{len(sample_urls)}")