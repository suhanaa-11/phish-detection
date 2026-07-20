# Known Limitations

## Brand Impersonation / Lookalike Domains

Testing found that `paypa1-security-alert.com` (a PayPal typosquat using 
digit "1" for letter "l") scored only 3/100 ("likely safe"). Current lexical 
features (URL length, entropy, digit count, special characters, IP presence, 
subdomain count) do not detect brand impersonation or lookalike domains. 
A planned future improvement is adding Levenshtein distance comparison 
against a list of known brand names to catch typosquatting patterns.

## Static Analysis (bandit)

Ran `bandit -r api/ ml/` — 0 issues identified across 408 lines of code.

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