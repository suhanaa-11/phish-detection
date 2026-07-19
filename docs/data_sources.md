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