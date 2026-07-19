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