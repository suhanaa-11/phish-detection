# Known Limitations & Red-Team Testing

## Adversarial Testing Methodology

After Phase 6, manual testing revealed that PhishGuard's lexical features
(trained on the Kaggle "Phishing Site URLs" dataset) missed several common
real-world evasion techniques. Rather than treating this as a single bug,
we ran a structured red-team pass across three attack categories and
tracked results through two rounds of fixes (v0.3.0, v0.4.0).

### Standing regression test suite

As the feature set and model evolved (v0.3.0 → v0.7.0), the following
14 URLs became a standing manual regression check, run after any
feature or model change: 7 real domains that must always score "safe"
(google.com/accounts/login, microsoft.com, reddit.com, stackoverflow.com,
paypal.com, wikipedia.org, facebook.com) and 7 constructed phishing
patterns that must always score "phishing" (a disposable-TLD + keyword
URL, a digit-swap Facebook typosquat, a brand-in-subdomain Apple
impersonation, a homoglyph Amazon typosquat, a Cyrillic homograph of
apple.com, a decimal-encoded IP, and a digit-swap PayPal typosquat).

This suite caught a real false positive in v0.5.0 (see below) before
it reached production, and confirms v0.7.0 passes all 14 cases.

### Attack categories tested

1. **IDN homograph attacks** — domains using visually identical Unicode
   characters (e.g. Cyrillic а/о) in place of Latin letters
2. **URL obfuscation** — IP addresses encoded as decimal integers or hex
   octets instead of standard dotted-decimal notation; percent-encoded
   hostnames
3. **Brand impersonation** — typosquats via character substitution
   (`paypa1`, `arnaz0n`) and brand names embedded as fake subdomains
   (`paypal.com.verify-account-security-check.xyz`)

### Results

| Attack pattern | v0.2.0 (before) | v0.4.0 (after) | Status |
|---|---|---|---|
| Cyrillic homograph (`аpple.com`) | 41, likely safe | 90, phishing | Fixed |
| Cyrillic homograph (`gооgle.com`) | 36, likely safe | 90, phishing | Fixed |
| Percent-encoded hostname | 73, phishing | 66, phishing | Already caught |
| Decimal-integer IP | 20, likely safe | 90, phishing | Fixed |
| Hex-octet IP | 35, likely safe | 90, phishing | Fixed |
| Brand name as fake subdomain (`.xyz`) | 34, likely safe | 91, phishing | Fixed |
| Digit-swap typosquat (`paypa1`) | 32, likely safe | 71, phishing | Fixed |
| Homoglyph typosquat (`arnaz0n`) | 75, phishing | 100, phishing | Improved confidence |
| Real domain: google.com | 36, likely safe | 35, likely safe | No false positive |
| Real domain: wikipedia.org | — | 34, likely safe | No false positive |
| Real domain: paypal.com | — | 35, likely safe | No false positive |

**8 of 8 tested attack patterns caught after fixes, with 0 false positives
introduced on legitimate domains.**

## v0.5.0 False Positive: A Lesson in Feature Risk

Adding `has_suspicious_tld` and `suspicious_keyword_count` in v0.5.0
improved ROC-AUC to 0.881 — the best raw number of any version. But the
standing regression suite caught a serious problem: `https://www.google.com/accounts/login`,
a completely legitimate URL, scored 98/100 "phishing."

**Root cause:** `suspicious_keyword_count` averaged only 0.0029 in the
legitimate ("good") class — meaning 75%+ of real URLs have a count of
exactly 0. When a real URL *did* contain 1-2 keywords (a normal
occurrence on login/account pages), XGBoost had almost no legitimate
examples to weigh against it, and learned an extreme split: SHAP analysis
showed this single feature contributing +5.23 to the prediction — larger
than every other feature's contribution combined.

**Fix (v0.6.0):** Removed `suspicious_keyword_count` from the trained
model entirely, keeping it only as a small, capped rule-based nudge
(+10 points, only when count >= 3) applied after the ML score. This
dropped ROC-AUC slightly (0.881 -> 0.860) but eliminated the false
positive — verified via the regression suite.

**Takeaway:** A feature with strong aggregate statistical separation
between classes is not automatically safe to hand to a tree-based model
without checking how it behaves on real edge cases. Rare-but-directional
signals need either enough positive examples to generalize safely, or
should stay outside the model as a capped, human-designed rule — the same
lesson learned with `has_obfuscated_ip` and `has_non_ascii` in v0.3.0/v0.4.0,
but this time the risk was a false positive on real traffic rather than a
missed detection, which is arguably the more costly failure mode for a
security tool.

## Root Cause

Investigation showed the model's lexical *features* weren't the problem —
they extracted correctly. The real issue was **training data sparsity**.
Checking how often each new signal appeared in the 549,346-row training set:

| Feature | Rows where true | % of "bad" (phishing) class |
|---|---|---|
| `has_obfuscated_ip` | 3 | 0.002% |
| `has_non_ascii` | 82 | more common in "good" class than "bad" |
| `brand_similarity_flag` | 1,923 | 0.7% |
| `brand_in_subdomain_flag` | 4,549 | 2.7% (34x more common than in "good") |

Gradient-boosted models like XGBoost can only learn a strong weight for a
feature if it appears often enough, on the correct side of the label, during
training. IP obfuscation and Unicode homographs are rare in this organically-
collected dataset — real-world attackers use them, but not commonly enough
here for the model to learn their significance on its own.

## Fix: Hybrid ML + Rule-Based Architecture

Rather than trying to force a model to learn from a handful of examples,
`ml/explain.py` now applies a rule-based override layer on top of the ML
score for signals that are rare in training data but near-deterministic
indicators of phishing in practice:

- **Hard override (floor of 90)**: `has_obfuscated_ip`, `has_non_ascii`,
  `brand_in_subdomain_flag` — these have very low false-positive risk, so
  when they fire, the score is forced to a high-confidence phishing range
  regardless of the model's raw prediction.
- **Partial boost (+25 points)**: `brand_similarity_flag` — this can
  plausibly fire on legitimate businesses with brand-adjacent names, so
  it nudges the score rather than forcing a floor, letting the model's
  other signals still contribute to the final verdict.

This is a deliberate design choice: pure ML for statistically-learnable
patterns, deterministic rules for rare-but-certain red flags that the
model can't yet learn from limited examples.

## Still Open

- **Brand list is hardcoded** (`KNOWN_BRANDS` in `ml/features/lexical.py`,
  16 entries) — doesn't scale to less common but still-targeted brands.
  A future version could pull from a maintained public list.
- **Homoglyph normalization is limited** to a fixed substitution table
  (`rn`→`m`, `0`→`o`, etc.) — doesn't cover the full range of Unicode
  confusable characters (see the IDN homograph feature `has_non_ascii`
  for the broader Unicode case, which is a separate, working signal).
- **Rule overrides are not yet covered by automated tests** — `tests/`
  currently tests the ML pipeline and API routes, but not the override
  logic in `ml/explain.py` directly. Planned as a follow-up.

## Static Analysis (bandit)

Ran `bandit -r api/ ml/` — 0 issues identified across 408 lines of code
(as of the last scan; line count will have grown with the new feature code).

**Known blind spot:** the codebase uses `joblib.load()` / `joblib.dump()` to
serialize the trained XGBoost model (`ml/train_xgboost.py`, `ml/explain.py`).
Bandit's default rule set (B301/B403) flags raw `pickle`/`cPickle` calls but
does not recognize `joblib`, even though joblib uses pickle-based serialization
internally for non-array Python objects. This means bandit did not flag a
real deserialization risk: loading a `.pkl` file from an untrusted source
via joblib could execute arbitrary code, identical to the risk with raw pickle.

In this project the model files are produced by our own training pipeline
and never loaded from user input, so the risk is currently accepted. If
model files were ever accepted from external sources (e.g. a plugin system),
this would need to be revisited — e.g. validating file provenance, restricting
`joblib.load` to a trusted volume, or moving to a non-pickle format
(ONNX, safetensors) for the model artifact.
## v0.7.0: False-Positive Rate Investigation and Threshold Tuning

### The problem

While investigating an unrelated dataset-augmentation experiment (see below),
false-positive analysis revealed something bigger: v0.7.0, running in
production, was flagging **17.11% of legitimate URLs** as phishing (measured
on a held-out split of the original 549,346-row dataset). The existing
14-case regression suite never caught this, because all 7 "safe" test cases
are short, root-domain URLs from famous brands (google.com, paypal.com,
etc.) — a shape that isn't representative of most of the "good" class.

Pulling the actual misclassified URLs (not just aggregate stats) showed a
clear pattern: false positives were concentrated in URLs with **real paths
and directory structure** — personal LinkedIn profiles, government
subpages, university course pages, niche business and nonprofit sites — not
the short root-domain shape the regression suite tests. A comparison sample
of 30 such URLs showed **26/30 (87%) already misclassified by v0.7.0**,
far above the 17% baseline rate, confirming this is a systematic gap in a
specific URL shape rather than evenly-distributed noise.

### Root cause (SHAP analysis)

Comparing mean SHAP contributions between false positives and correctly-
classified legitimate URLs (n=1,000 each) showed `digit_count` and
`special_char_count` as the dominant drivers:

| Feature | False positives (mean) | Correct good URLs (mean) |
|---|---|---|
| `digit_count` | 2.23 | 3.32 |
| `special_char_count` | 0.82 | 2.42 |

The model had learned "simple, clean URLs (few digits, few symbols) are
more likely phishing" — true on average, since attackers often craft
short, clean-looking convincing domains. But that same shape also
describes a large, ordinary category of the real internet (static pages,
older-style sites, simple directory structures). Lexical features alone
can't distinguish "genuinely simple, legitimate site" from "attacker kept
it simple on purpose" — the same fundamental limitation behind the
`paypa1-security-alert.com`-style typosquat cases documented above.

### Dead ends investigated (and why)

**Domain-age / WHOIS lookup** (`ml/features/domain.py`, built in Phase 2,
never wired in) was the obvious candidate — domain age is a genuinely new
signal lexical features can't express. Tested on a stratified sample of
300 "good" + 300 "bad" URLs before committing to a full-dataset extraction:
**0/600 lookups succeeded** — WHOIS servers rate-limited or blocked the
requests outright (timeouts, connection refusals, DNS failures) rather
than returning "no record." Even if this were solved (e.g. a paid WHOIS
API), there's a deeper flaw: the dataset is historical, and many phishing
domains from it have since expired and been re-registered by unrelated
legitimate owners — a live lookup today would measure the wrong thing for
a meaningful fraction of the "bad" class. Not pursued further.

**Path depth** (hypothesis: real sites have deeper, more varied path
structure than shallow fake phishing paths like `/login`) was tested
directly on the full dataset before adding it as a feature:

| | Mean path depth | % bare domain (0 segments) |
|---|---|---|
| good | 2.03 | 12.3% |
| bad | 2.28 | 9.7% |

The direction was the **opposite** of the hypothesis — bad URLs had
slightly higher path depth and lower bare-domain rate than good. Not a
usable signal; dropped.

### Fix: threshold tuning

Rather than a new feature, the fix was recalibrating the decision
threshold. Sweeping thresholds on the raw model's held-out predictions:

| Threshold | FP rate (good) | Recall (bad) | Precision (bad) |
|---|---|---|---|
| 0.50 (previous) | 17.11% | 71.62% | 62.49% |
| 0.60 (adopted) | 8.83% | 61.61% | 73.54% |
| 0.70 | 4.69% | 53.67% | 82.00% |
| 0.80 | 2.47% | 46.58% | 88.26% |

Chose **0.60** as a deliberately moderate point: roughly halves the
false-positive rate while retaining the majority of phishing recall.
Raising the threshold further (0.70+) would cut recall too aggressively
for a security tool. This is a **real, honest tradeoff, not a free
improvement** — the tool now misses more actual phishing than before in
exchange for far fewer false alarms on legitimate sites.

Raising the threshold required a corresponding change to the
`brand_similarity_flag` override boost (**+40 → +50** — see note in the
Hybrid ML + Rule-Based Architecture section above, which still shows the
original +25 value from v0.4.0's initial design) so existing typosquat
detections (`faceb00k-account-recovery-help.net`, `paypa1-security-
alert.com`) retained adequate margin above the new threshold instead of
silently falling below it.

**Final full-pipeline numbers** (threshold + all rule overrides, held-out
test split):

| Metric | Before | After |
|---|---|---|
| FP rate on legit URLs | 17.11% | **8.80%** |
| Phishing recall | 71.62% | **63.60%** |
| Phishing precision | 62.49% | **74.20%** |

14/14 on the regression suite maintained throughout, with healthier
margins than before (e.g. `faceb00k-account-recovery-help.net` moved from
a fragile 48-53 to a confident 63).

### Takeaway

The overrides built for rare-but-certain signals (obfuscated IPs,
homographs, brand-in-subdomain) barely move aggregate metrics — they're
too infrequent in the dataset to shift dataset-wide averages, even though
they're essential for the specific adversarial cases they target. This
means aggregate metrics alone can hide both problems (the 17.11% FP rate)
and fixes (the override layer's real value) — the regression suite and
targeted diagnostic scripts, not the confusion matrix alone, are what
actually validate model behavior.

## Dataset Augmentation Experiment (Investigated, Not Shipped)

### Motivation

Testing showed real high-traffic domains (google.com, facebook.com, etc.)
scored higher than ideal even when correctly classified "safe" — e.g.
`google.com/accounts/login` at 36/100. Hypothesis: the training data
underrepresents well-known, high-traffic legitimate domains structurally.
Tested augmenting the training set with ~10,000–100,000 real domains from
the Tranco top-sites list, labeled "good."

### First attempt: bare domains — backfired

Initial augmentation injected domains as bare strings (`google.com`, no
scheme or path). At 10,000 domains, aggregate metrics looked flat
(ROC-AUC 0.868 vs baseline 0.869). At 100,000 domains, ROC-AUC rose to
0.882 — but the regression suite's real-domain scores moved in the
**wrong** direction (e.g. `stackoverflow.com` 42 → 48, two points from
being misclassified). SHAP analysis showed `special_char_count` — sitting
at value 0 — contributing a *large positive push toward "phishing"* on
these URLs, despite being the same feature that should indicate "clean,
harmless." Root cause: injecting ~99,000 rows that all shared one narrow,
artificial feature-shape (bare domain: zero digits, zero special chars,
short length) created a dense cluster that distorted the tree's decision
boundary elsewhere, rather than teaching the model anything generalizable
about real high-traffic sites.

### Second attempt: varied URL shapes — real but partial improvement

Rebuilt the augmentation using 10 URL templates varying scheme, `www.`,
and path (`https://{domain}/login`, `https://www.{domain}/about`, etc.).
This fixed the safe-domain confidence problem cleanly and consistently
(e.g. `google.com/accounts/login` 36 → 27, `facebook.com` 38 → 17,
`wikipedia.org` 29 → 20) — a genuine, non-noise improvement across all 7
regression-suite safe cases. But it introduced a real tradeoff: `bad`
(phishing) precision dropped (0.62 → 0.57), and the `paypa1-security-
alert.com` typosquat's safety margin shrank (score 79 → 59, still
correctly caught but with much less headroom).

### Investigating the precision drop

False-positive analysis on the augmented model's held-out test set (17,253
false positives) showed **89% (15,360) came from the original dataset**,
not the newly-added augmented rows — meaning augmentation made the model
*worse* on pre-existing legitimate URLs, not just less effective on new
ones. Root cause: 9 of the 10 URL templates produced `special_char_count
= 0` (no hyphens, `&`, `=`, or `?` anywhere in the paths chosen), so even
"varied" shapes mostly collapsed onto the same feature-space region as the
original bare-domain bug, just less extremely.

Added 6 more templates with hyphenated slugs, multi-param query strings,
and numeric path segments to fix the character-composition gap. This did
**not** meaningfully help (original-dataset false positives: 15,360 →
15,735, essentially flat) — and comparing the exact same specific rows
across both training runs showed **the same URLs failing consistently**
regardless of template design (e.g. `whitehouse.gov/about/presidents/`,
several `linkedin.com/in/...` profiles, university subpages). This
indicates a genuine, structural overlap in lexical feature-space between
certain legitimate long-tail URLs and certain phishing URLs — not a fixable
template-design bug.

**Comparing against the v0.7.0 baseline directly on this same URL sample
was also important**: 26 of 30 were *already* misclassified by v0.7.0
before any augmentation — meaning most of what looked like an
augmentation-caused regression was actually a pre-existing production
issue the augmentation experiment happened to surface (see the threshold-
tuning section above for the actual fix to that problem).

### Status: not shipped

The augmented-experiment model remains uncommitted (`ml/models/
augmented_experiment/`, not a `vX.Y.Z`-named folder, so it is not
auto-loaded by `ml/explain.py`). It offers a real improvement in
confidence on major real-world domains but at a precision cost elsewhere,
and the underlying false-positive pattern it exposed was addressed
separately via threshold tuning rather than via the augmented dataset
itself. Revisiting this is lower priority than the domain-age/WHOIS
route once that becomes practically viable (see dead-end note above), or
could be reconsidered later with a training approach that weights
augmented rows to avoid dominating the boundary rather than simple
concatenation.
