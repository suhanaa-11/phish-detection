# Data Sources

## Phishing & Legitimate URL Dataset

- **Source:** Kaggle — "Phishing Site URLs" dataset
- **Downloaded:** July 2026
- **File:** `data/raw/phishing_urls.csv` (not committed to Git — see `.gitignore`)
- **Rows:** 549,346
- **Columns:** `URL` (string), `Label` (`good` / `bad`)
- **Class balance:** 392,924 legitimate (`good`), 156,422 phishing (`bad`)
- **Note:** Raw file excluded from version control due to size (~31MB). To reproduce,
  download from Kaggle and place at `data/raw/phishing_urls.csv`.

## Processed Features

- **Script:** `ml/features/build_dataset.py`
- **Output:** `data/processed/features.csv` (not committed — regenerate via script)
- **Shape:** 549,346 rows × 8 columns (7 lexical features + label)
- **Note:** Domain-age/WHOIS features excluded from the full run due to network
  lookup time (~549k sequential lookups would take hours and risk rate-limiting).
  WHOIS features are implemented and demonstrated on a small sample instead
  (see `ml/features/domain.py`).