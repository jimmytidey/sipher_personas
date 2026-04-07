# Data processing

## Pipeline

Sub-steps use letter suffixes (`3a`, `3b`, …): **`a`** = main transform, **`b`** (and later letters) = optional validation / reports on the same stage output.

| Step | Notebook                       | Output                                                     | Validate with                   |
| ---- | ------------------------------ | ---------------------------------------------------------- | ------------------------------- |
| 1    | `1_pickle_sipher.ipynb`        | `sipher_optimized.pkl`, `sipher_unique_pidp.pkl`           | —                               |
| 2    | `2_pickle_ukhls_waves.ipynb`   | `data/2_pickle_ukhls_waves/{wave}_indresp_optimized.pkl`   | —                               |
| 3a   | `3a_backfill_ukhls_waves.ipynb` | `data/3_backfill_ukhls_waves/o_indresp_backfilled.pkl`     | `3b_visualise_backfill.ipynb`    |
| 3b   | `3b_visualise_backfill.ipynb`  | `data/3_backfill_ukhls_waves/backfill_visualisation.png`  | —                               |
| 4a   | `4a_feature_eng_ukhls.ipynb`    | `data/4_feature_eng_ukhls/o_indresp_feature_eng.pkl`       | `4b_visualise_feature_eng.ipynb` |
| 4b   | `4b_visualise_feature_eng.ipynb` | `data/4_feature_eng_ukhls/feature_eng_visualisation.png` | —                               |
| 5a   | `5a_derive_variables.ipynb`     | `data/5_derive_variables/o_indresp_derived.pkl`          | `5b_visualise_derived_variables.ipynb` |
| 5b   | `5b_visualise_derived_variables.ipynb` | `data/5_derive_variables/derived_visualisation.png` | —                               |
| 6a   | `6a_synthetic_population.ipynb` | `data/6_synthetic_population/synthetic_population.parquet` | —                               |
| 6b   | `6b_synthetic_vs_ukhls.ipynb`  | `data/6b_synthetic_vs_ukhls/` (plots + CSV)                | UKHLS website stats (paste in notebook) |
| 7    | `7_cluster_local_level.ipynb`  | `data/7_cluster_local_level/LA_*_clusters.csv`               | —                               |
| 8    | `8_cluster_national_level.ipynb` | `data/8_cluster_national_level/LA_*_national_clusters.csv` | —                               |
| 9    | `9_group_averages.ipynb`       | `data/9_group_averages/group_baselines.csv`, `group_distributions.csv` | —                    |
| 10   | `10_label_local_level_clusters.ipynb`  | `data/7_cluster_local_level/*_described.csv` (LLM labels)   | —                       |
| 11   | `11_label_national_level_clusters.ipynb` | `data/8_cluster_national_level/*_described.csv` (LLM labels) | —                     |
| 12   | `12_generate_portraits.ipynb`  | `api/data/portraits/`                                      | —                               |
| 13   | `13_nl_profiles.ipynb`         | `data/13_nl_profiles/nl_profiles.csv`                      | —                               |

## Data folder structure (main artefacts)

```
data/
├── raw/
│   ├── sipher/
│   └── ukhls/
├── 1_pickle_sipher/
├── 2_pickle_ukhls_waves/
├── 3_backfill_ukhls_waves/
├── 4_feature_eng_ukhls/
├── 5_derive_variables/              ← o_indresp_derived.pkl, derived_visualisation.png
├── 6_synthetic_population/
├── 6b_synthetic_vs_ukhls/
├── 7_cluster_local_level/
├── 8_cluster_national_level/
└── 9_group_averages/
```

## Notes

- Variable definitions are merged in `data_pipeline/config_variables.py` (theme modules + `config_variables_derived.py` for composites).
- Step 5a maps digital and service inputs to 0–1 component scores and averages them — see `data_pipeline/helpers/derive_variables.py`.
- K-Means inputs are `config_cluster.CLUSTER_VARS`; tribe DNA / summaries use all `VARIABLES` including `digital_use` and `service_use`.
- Step 7 clusters each geography unit independently (local). Step 8 fits one set of clusters on all UKHLS respondents nationally, then assigns each synthetic person to a national cluster; the UI `mode=national` switch loads step 8's output.
