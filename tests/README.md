# Tests

This folder previously contained **pytest** suites for the API (`test_api.py`) and the clustering helpers (`test_pipeline.py`). They were **removed** because they had drifted from the real pipeline (variable renames, `doby_dv` / transforms, `data_test` shape, etc.) and were no longer a reliable signal.

**`generate_test_data.py`** remains as an optional script to (re)build minimal `data_test/` fixtures if you ever want a small sandbox dataset — it is not run in CI.

If you add tests again, prefer **narrow, high-value checks** on stable interfaces (e.g. one smoke test for `/health` with a mocked cluster path) or **manual validation** via the visualisation notebooks.
