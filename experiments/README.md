# Experiments

Investigated approaches that did not ship to production, kept as
reproducible reference material. None of these scripts are imported by
`api/`, `ml/explain.py`, or the extension — they're standalone, run
manually, and document methodology for findings in `docs/limitations.md`.

## augmentation/
Dataset augmentation with real-world domains (Tranco top-sites list) to
improve model confidence on high-traffic legitimate URLs. Found a real
improvement on major domains, but with a precision tradeoff elsewhere
that wasn't clearly better than a plain threshold adjustment (which
shipped instead — see `ml/explain.py` and `docs/limitations.md`).
Model artifact intentionally not committed (`ml/models/augmented_experiment/`,
gitignored).

## false_positive_investigation/
Diagnostic scripts used to root-cause v0.7.0's 17.11% false-positive
rate, including two dead-end hypotheses (domain-age/WHOIS lookup,
path-depth as a feature) that were tested and ruled out before the
threshold-tuning fix that did ship.

## tfidf/
Character n-gram TF-IDF experiment from an earlier phase. Achieved a
high raw ROC-AUC (0.986) but failed the standing regression suite badly
(8/14) due to overfitting — documented as a negative result in
`docs/limitations.md`.

Run any script from the repo root, e.g.:
