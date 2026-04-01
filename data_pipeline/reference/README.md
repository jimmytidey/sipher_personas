# UKHLS reference extracts

## `ukhls_continuous_reference.csv`

Pasted summary statistics from the UKHLS / Understanding Society tools (or similar) for comparison with the synthetic population or pipeline outputs.

- **`doby_dv`:** The UKHLS table typically reports **derived age** (years), not raw birth year. The pipeline stores `doby_dv` as year of birth and applies `birth_year_to_age` in feature engineering, so the resulting age distribution should be **roughly comparable** to the reference row in this file (same N/wave caveats apply).

## `ukhls_categorical/` — one CSV per variable

Each file is named `{variable_code}.csv` (e.g. `racel_dv.csv`). Columns:

| Column          | Meaning |
|-----------------|--------|
| `category_code` | Numeric code as in `config_variables.py` (`categories` / `group_labels`) |
| `label`         | Label copied from config (for alignment — do not edit unless UKHLS uses different wording) |
| `percent`       | UKHLS frequency as **percentage 0–100** (paste from website) |
| `n`             | Optional weighted or raw count if your table provides it |

**Regenerate row scaffolding** after changing labels in config:

```bash
python data_pipeline/reference/build_ukhls_categorical_templates.py
```

That overwrites CSVs — copy your pasted `percent` / `n` values first, or commit before re-running.

Variables with `categorical: True` but no `categories` / `group_labels` in config (e.g. `nbrsnci_dv`) do not get a file; add a custom CSV by hand if needed.

- **`racel_dv.csv`** — UKHLS figures **after** applying the same collapse as `recode` in `config_variables.py` (`racel_dv`). You can paste collapsed totals here, or leave **White** / **Mixed** empty: step **6b** fills missing `percent` cells by **aggregating `racel_raw_ukhl.csv`** with `RECODE_MAPS["racel_dv"]` (same remapping as feature engineering). Raw UKHLS frequency tables (all ethnic codes) are in **`racel_raw_ukhl.csv`**. Raw code **3** (Gypsy / Irish Traveller) maps to collapsed **White** (`recode` → `1.0`).

- **`hiqual_dv.csv`** — Qualification scale aligned with **`group_labels`** in `config_variables.py`: raw code **9** (No qualification) is stored as **`6.0`** to match `recode` {9 → 6}. **`hiqual_raw_ukhl.csv`** keeps UKHLS code **9** for the same row. **N = 32,849** (includes missing / inapplicable).
