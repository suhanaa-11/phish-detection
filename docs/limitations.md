# Known Limitations & Red-Team Testing

## Adversarial Testing Methodology

After Phase 6, manual testing revealed that PhishGuard's lexical features
(trained on the Kaggle "Phishing Site URLs" dataset) missed several common
real-world evasion techniques. Rather than treating this as a single bug,
we ran a structured red-team pass across three attack categories and
tracked results through two rounds of fixes (v0.3.0, v0.4.0).

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