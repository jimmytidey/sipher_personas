# Data processing

## Pipeline

| Step | Notebook                       | Output                                                     | Validate with                   |
| ---- | ------------------------------ | ---------------------------------------------------------- | ------------------------------- |
| 1    | `1_pickle_sipher.ipynb`        | `data/1_pickle_sipher/sipher_optimized.pkl`                | —                               |
| 2    | `2_pickle_ukhls_waves.ipynb`   | `data/2_pickle_ukhls_waves/{wave}_indresp_optimized.pkl`   | —                               |
| 3    | `3_backfill_ukhls_waves.ipynb` | `data/3_backfill_ukhls_waves/o_indresp_backfilled.pkl`     | `3_visualise_backfill.ipynb`    |
| 4    | `4_feature_eng_ukhls.ipynb`    | `data/4_feature_eng_ukhls/o_indresp_feature_eng.pkl`       | `4_visualise_feature_eng.ipynb` |
| 5    | `5_normalise_ukhls.ipynb`      | `data/5_normalise_ukhls/normalized.pkl`                    | `5_visualise_normalise.ipynb`   |
| 6    | `6_cluster.ipynb`              | `data/6_cluster/tribe_dna.csv`                             | —                               |
| 7    | `7_synthetic_population.ipynb` | `data/7_synthetic_population/synthetic_population.parquet` | —                               |

## Data folder structure

```
data/
├── raw/
│   ├── sipher/                      ← source CSV (not committed — place sipher.csv here)
│   └── ukhls/                       ← source .tab files (not committed)
├── 1_pickle_sipher/                 ← sipher_optimized.pkl
├── 2_pickle_ukhls_waves/            ← {wave}_indresp_optimized.pkl  (one per wave)
├── 3_backfill_ukhls_waves/          ← o_indresp_backfilled.pkl + variable_distributions.png
├── 4_feature_eng_ukhls/             ← o_indresp_feature_eng.pkl + feature_eng_distributions.png
├── 5_normalise_ukhls/               ← normalized.pkl + normalised_distributions.png
├── 6_cluster/                       ← tribe_dna.csv + pidp_tribe.pkl
└── 7_synthetic_population/          ← synthetic_population.parquet (52M rows, snappy-compressed)
```

## Notes

- All variable definitions, clip/floor/recode rules are in `data_processing/config_variables.py`
- Step 4 applies all `recode`, `floor`, and `clip` values from `config_variables.py` and selects `cluster=True` features only
- Step 5 is purely Z-score (StandardScaler) — no manual mappings
- Step 6 reads both the normalised matrix (for clustering) and the feature-eng real values (for the DNA report)
- Step 7 joins the normalised feature vectors onto the full SIPHER synthetic population (52M rows) ready for regional clustering
