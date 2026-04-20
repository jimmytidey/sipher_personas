# Data processing

## Pipeline

Sub-steps use letter suffixes (`3a`, `3b`, …): **`a`** = main transform, **`b`** (and later letters) = optional validation / reports on the same stage output.

| Step | Notebook                       | Output                                                     | Validate with                   |
| ---- | ------------------------------ | ---------------------------------------------------------- | ------------------------------- |
| 1    | `1_pickle_sipher.ipynb`        | `sipher_optimized.pkl`, `sipher_unique_pidp.pkl`           | —                               |
| 2    | `2_pickle_ukhls_waves.ipynb`   | `data/2_pickle_ukhls_waves/{wave}_indresp_optimized.pkl`   | —                               |
| 3a   | `3a_backfill_ukhls_waves.ipynb` | `data/3_backfill_ukhls_waves/{WAVE}_indresp_backfilled.pkl` (`config_variables.WAVE`, default **k**) | `3b_visualise_backfill.ipynb`    |
| 3b   | `3b_visualise_backfill.ipynb`  | `data/3_backfill_ukhls_waves/backfill_visualisation.png`  | —                               |
| 4a   | `4a_feature_eng_ukhls.ipynb`    | `data/4_feature_eng/{WAVE}_feature_eng.pkl`, `{WAVE}_feature_eng.csv` (`config_variables.WAVE`) | `4b_visualise_feature_eng.ipynb` |
| 4b   | `4b_visualise_feature_eng.ipynb` | reads `4_feature_eng/{WAVE}_feature_eng.pkl`; plot saved next to notebook (e.g. `./4c_feature_eng_visualisation.png`) | —                               |
| 5    | `5_add_nl_strings.ipynb`       | `data/5_add_nl_strings/{WAVE}_with_nl_profile.pkl` + `.csv`; also updates `4_feature_eng/{WAVE}_feature_eng.pkl` for step 6 | —                               |
| 6    | `6_add_vector_embedding.ipynb` | `data/6_add_vector_embedding/{WAVE}_vector_embedding.pkl` + `.csv`; `data/6_embeddings/` (npy + index + parquet for step 8) | —                               |
| 7    | `7_sipher_row_counts.ipynb`    | `data/7_sipher_row_counts/sipher_pidp_counts.parquet` (+ `.csv`; optional `sipher_zone_pidp_counts.*` if `synthetic_zone` exists) | — |
| 8b\* | `8b_cluster_national_level.ipynb` | **First run (before 7a):** national K-Means on UKHLS → `8_cluster_national_level/{WAVE}_national_pidp_assignments.parquet`; Phase 2 skipped until synpop exists. **Second run (after 7a):** Phase 1 skipped if cache fresh; writes `LA_*_national_clusters.csv`. | —        |
| 7a   | `7a_synthetic_population.ipynb` | `data/7_synthetic_population/synthetic_population.parquet` | —                               |
| 7b   | `7b_synthetic_vs_ukhls.ipynb`  | `data/7b_synthetic_vs_ukhls/` (plots + CSV)                | UKHLS website stats (paste in notebook) |
| 7c   | `7c_nan_report.ipynb`          | NaN coverage report                                        | —                               |
| 8    | `8_cluster_embeddings.ipynb`   | `data/8_embedding_clusters/LA_embedding_clusters.csv` (+ intermediates; LA mode needs 7a synpop) | —           |
| 9    | `9_group_averages.ipynb`       | `data/9_group_averages/local_group_*.csv`                 | —                               |
| 10   | `10_label_local_level_clusters.ipynb` | `*_described.csv` beside step-8 export              | —                               |
| 11   | `11_generate_portraits.ipynb`  | `api/data/portraits/`                                      | —                               |

**Archived (not in `0_run_pipeline`):** `KEEP/5a_derive_variables.ipynb`, `KEEP/5b_visualise_derived_variables.ipynb` — optional derived composites (`digital_use`, `service_use`, etc.); same logic as `helpers/derive_variables.py`.

## Data folder structure (main artefacts)

```
data/
├── raw/
│   ├── sipher/
│   └── ukhls/
├── 1_pickle_sipher/
├── 2_pickle_ukhls_waves/
├── 3_backfill_ukhls_waves/
├── 4_feature_eng/                  ← {WAVE}_feature_eng.pkl + .csv (4a); updated by KEEP/5a, step 5
├── 5_add_nl_strings/               ← {WAVE}_with_nl_profile.pkl + .csv (step 5)
├── 6_add_vector_embedding/         ← {WAVE}_vector_embedding.pkl + .csv (step 6)
├── 6_embeddings/                   ← npy + index + parquet (step 6; consumed by step 8)
├── 7_sipher_row_counts/
├── 7_synthetic_population/
├── 7b_synthetic_vs_ukhls/
├── 8_cluster_national_level/       ← {WAVE}_national_pidp_assignments.parquet (8b cache) + LA_*_national_clusters.csv
├── 8_embedding_clusters/
└── 9_group_averages/
```

## Notes

- **\*8b run order:** `0_run_pipeline` runs **`7_sipher_row_counts.ipynb`** after step 6 (SIPHER donor / zone×donor multiplicity; needs step 1 only), then executes `8b_cluster_national_level.ipynb` **before** `7a` and **again** after `7a` so national clustering uses only UKHLS through step 6, while LA persona CSVs still join the synthetic population.
- **Primary UKHLS wave** is `config_variables.WAVE` (default **`k`**): backfill and all `k_*` / `k_*_eng` columns follow this. Wave **k** matches the full SIPHER-linked UKHLS cohort (~27.3k rows in step 2); newer waves (e.g. **o**) are smaller and used only as backfill sources when present.
- Variable definitions are merged in `data_pipeline/config_variables.py` (theme modules + `config_variables_derived.py` for composites).
- Optional `KEEP/5a` maps digital and service inputs to 0–1 component scores — see `data_pipeline/helpers/derive_variables.py`.
- K-Means inputs are `config_variables.CLUSTER_VARS`; tribe DNA / summaries use all `VARIABLES` including `digital_use` and `service_use` when those columns exist.
- The web app loads persona rows from `LA_embedding_clusters.csv` (step 8) or `LA_*_national_clusters.csv` (step 8b) depending on mode, optionally `*_described.csv` after labelling, under `api/data/clusters/` or the pipeline output folder.
