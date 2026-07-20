# Model Evaluation

## Dataset
- 549,346 URLs (392,924 legitimate, 156,422 phishing)
- Features: 7 lexical URL features (length, entropy, digit count, special chars, IP presence, subdomain count, HTTPS usage)
- Split: 80/20 train/test, stratified by label

## Baseline: Logistic Regression
- ROC-AUC: 0.693
- Phishing (bad) precision: 0.45, recall: 0.51, F1: 0.47

## XGBoost (v0.1.0)
- ROC-AUC: 0.855
- Phishing (bad) precision: 0.60, recall: 0.71, F1: 0.65
- 300 estimators, max_depth=6, learning_rate=0.1, scale_pos_weight balanced for class imbalance

## Takeaway
XGBoost substantially outperforms the linear baseline on the same feature set,
improving ROC-AUC by +0.16. Remaining false negatives (9,168 phishing URLs
missed) are a target for future feature additions (domain age, lookalike-domain
detection, content-based signals) in later iterations.

## Known Limitations
- Model relies only on lexical URL patterns; sophisticated phishing sites using
  clean, short URLs (e.g., URL shorteners, compromised legitimate domains) are
  harder to catch with this feature set alone.
- No content-based or domain-age signals yet (planned for Phase 4).

## Model v0.2.0 — Bug Fix: HTTPS Feature Data Leakage

**Issue found:** SHAP analysis revealed `has_https` contributed an outsized, backwards
signal (+3.53 impact vs <0.6 for all other features) causing legitimate HTTPS sites
(e.g. wikipedia.org) to be scored 95/100 "phishing."

**Root cause:** Investigation of the raw dataset showed only 88 of 549,346 URLs
included an explicit `https://` scheme, and all 88 happened to be labeled `bad` by
chance — the vast majority of URLs in both classes had no scheme prefix at all.
The model learned a spurious correlation from this near-constant, sparse feature
rather than a real security signal.

**Fix:** Retrained excluding `has_https` from the feature set (v0.2.0).

**Result:** ROC-AUC unchanged (0.8554 → 0.8554), confirming the feature added no
real predictive value — removing it eliminated the false-positive pattern without
any accuracy cost. Verified: wikipedia.org now scores 35 ("likely safe") instead
of 95 ("phishing").