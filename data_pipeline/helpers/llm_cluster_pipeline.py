"""Shared pipeline helpers for LLM-based local-authority clustering notebooks
(14_llm_cluster_LA_gemini and 15_llm_cluster_LA_claude).
"""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path

import pandas as pd

from data_pipeline.helpers.llm_prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
    sanitise_name,
)

# ── Profile encoding ──────────────────────────────────────────────────────────

def make_profile_cols(wave: str) -> list[tuple[str, str]]:
    """Return ordered (column_name, short_code) pairs for compact profile encoding."""
    return [
        (f"{wave}_doby_dv_eng", "age"),
        (f"{wave}_sex_dv",      "sex"),
        (f"{wave}_racel_dv",    "eth"),
        (f"{wave}_hiqual_dv",   "edu"),
        (f"{wave}_jbstat",      "emp"),
        (f"{wave}_marstat_dv",  "mar"),
        (f"{wave}_tenure_dv",   "ten"),
        (f"{wave}_hhtype_dv",   "hh"),
        (f"{wave}_scsf1",       "health"),
    ]


def encode_profile(row, profile_cols: list[tuple[str, str]], avail_cols: list[str]) -> str:
    """Encode a DataFrame row as a compact pipe-separated string of numeric codes."""
    parts = []
    for col, _ in profile_cols:
        if col not in avail_cols:
            parts.append("?")
            continue
        v = row[col]
        try:
            fv = float(v)
            parts.append("?" if (pd.isna(fv) or fv < 0) else str(int(fv)))
        except (TypeError, ValueError):
            parts.append("?")
    return "|".join(parts)


# ── Data loading ──────────────────────────────────────────────────────────────

def load_and_prepare(
    nl_profile_path: Path,
    la_counts_path: Path,
    hier_col: str | None,
    wave: str,
    test_mode: bool = False,
    test_la_codes: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Load NL profiles and LA counts, merge, apply group filter, and encode
    compact profiles.

    Returns:
        df_nl              – raw NL profile table (for feature lookup later)
        df_merged          – merged + filtered + encoded table
        avail_profile_cols – profile columns actually present in df_nl
    """
    profile_cols = make_profile_cols(wave)

    print("\nLoading NL profiles …", flush=True)
    df_nl = pd.read_pickle(nl_profile_path)
    df_nl["pidp"] = pd.to_numeric(df_nl["pidp"], errors="coerce").astype("int64")
    print(f"  {len(df_nl):,} respondents loaded.", flush=True)

    avail_profile_cols = [col for col, _ in profile_cols if col in df_nl.columns]
    missing_cols       = [col for col, _ in profile_cols if col not in df_nl.columns]
    if missing_cols:
        print(f"  Warning: missing profile columns (will encode as ?): {missing_cols}", flush=True)
    print(f"  Profile columns available: {len(avail_profile_cols)}/{len(profile_cols)}", flush=True)

    print("Loading LA counts …", flush=True)
    df_la = pd.read_csv(
        la_counts_path,
        dtype={"pidp": "int64", "ladcd": str, "ladnm": str, "n": "int64"},
    )
    print(f"  {len(df_la):,} rows, {df_la['ladcd'].nunique():,} LAs loaded.", flush=True)

    if test_mode and test_la_codes:
        df_la = df_la[df_la["ladcd"].isin(test_la_codes)].copy()
        print(
            f"  TEST MODE — {df_la['ladcd'].nunique()} LA(s): "
            f"{sorted(df_la['ladnm'].unique().tolist())}",
            flush=True,
        )

    keep_cols = ["pidp"] + avail_profile_cols
    if hier_col:
        if hier_col not in df_nl.columns:
            raise ValueError(f"hier_col '{hier_col}' not found in NL profile table")
        if hier_col not in keep_cols:
            keep_cols.append(hier_col)

    df_merged = df_la.merge(df_nl[keep_cols], on="pidp", how="inner")
    if hier_col:
        df_merged.rename(columns={hier_col: "group"}, inplace=True)
        n_before  = len(df_merged)
        df_merged = df_merged[
            df_merged["group"].notna() & (df_merged["group"] >= 0)
        ].copy()
        n_dropped = n_before - len(df_merged)
        if n_dropped:
            print(f"  Dropped {n_dropped:,} rows with missing/unknown group value.", flush=True)
    print(f"  Merged: {len(df_merged):,} rows", flush=True)

    print("  Building compact profile encodings …", flush=True)
    df_merged["compact_profile"] = df_merged[avail_profile_cols].apply(
        lambda row: encode_profile(row, profile_cols, avail_profile_cols), axis=1
    )
    print(f"  Unique compact profiles: {df_merged['compact_profile'].nunique():,}", flush=True)

    return df_nl, df_merged, avail_profile_cols


# ── Group / allocation helpers ────────────────────────────────────────────────

def build_groups(df_merged: pd.DataFrame, hier_col: str | None) -> pd.DataFrame:
    """Return DataFrame of unique LA × group combinations."""
    group_by   = ["ladcd", "ladnm", "group"] if hier_col else ["ladcd", "ladnm"]
    all_groups = df_merged[group_by].drop_duplicates().reset_index(drop=True)
    print(f"\n{len(all_groups)} LA×group combination(s) to process:")
    print(all_groups.to_string(index=False))
    return all_groups


def compute_cluster_allocations(
    df_merged: pd.DataFrame,
    hier_col: str | None,
    n_clusters_local: int,
    lp_module,
) -> dict:
    """Pre-compute proportional cluster counts per LA × group via
    largest-remainder allocation.

    Returns la_k_map: {(ladcd, group): k}
    """
    if not hier_col:
        return {}

    la_group_pop = (
        df_merged.groupby(["ladcd", "group"], sort=False)["n"]
        .sum()
        .reset_index()
        .rename(columns={"n": "pop"})
    )
    la_k_map: dict = {}
    for ladcd, grp in la_group_pop.groupby("ladcd"):
        pop_dict = dict(zip(grp["group"], grp["pop"]))
        budget   = n_clusters_local * len(pop_dict)
        allocs   = lp_module.allocate_clusters(pop_dict, budget, min_per_group=3, max_per_group=8)
        for g, k_alloc in allocs.items():
            la_k_map[(ladcd, g)] = k_alloc

    print("\nCluster allocations per LA × group:")
    for (ladcd, g), k_alloc in sorted(la_k_map.items()):
        label = lp_module.resolve_emp_label(g) or g
        print(f"  {ladcd}  {label:<30} → {k_alloc} clusters")

    return la_k_map


def build_resume_state(
    all_groups: pd.DataFrame,
    api_out: Path,
    hier_col: str | None,
) -> tuple[pd.DataFrame, int, int, int]:
    """Determine which LA×group combos are already done by inspecting api_out.

    Returns (to_run, n_done, n_total, n_remain).
    """
    if api_out.exists():
        done_df = pd.read_csv(
            api_out, usecols=["ladcd"] + (["group"] if hier_col else [])
        )
        if hier_col:
            done_pairs = set(
                zip(done_df["ladcd"].astype(str), done_df["group"].astype(str))
            )
            mask_done = all_groups.apply(
                lambda r: (str(r["ladcd"]), str(r["group"])) in done_pairs, axis=1
            )
        else:
            done_ladcds = set(done_df["ladcd"].unique())
            mask_done   = all_groups["ladcd"].isin(done_ladcds)
        n_done_init = int(mask_done.sum())
        print(f"\n  Resuming — {n_done_init} LA×group(s) already done.")
    else:
        mask_done = pd.Series(False, index=all_groups.index)

    to_run   = all_groups[~mask_done].copy()
    n_done   = len(all_groups) - len(to_run)
    n_total  = len(all_groups)
    n_remain = len(to_run)

    print(f"\n{'='*60}")
    print(f"  Progress: {n_done} / {n_total} done  ({n_remain} remaining)")
    if n_remain > 0 and n_done > 0:
        done_names = all_groups[mask_done]["ladnm"].unique()
        preview    = ", ".join(done_names[:5].tolist())
        suffix     = " …" if len(done_names) > 5 else ""
        print(f"  Already done: {preview}{suffix}")
    print(f"{'='*60}")

    return to_run, n_done, n_total, n_remain


# ── Schema ────────────────────────────────────────────────────────────────────

_CATEG_BASES = [
    "sex_dv", "jbstat", "racel_dv", "hiqual_dv",
    "marstat_dv", "tenure_dv", "hhtype_dv",
]


def make_summary_cols(leading: list[str]) -> list[str]:
    """Build the fixed SUMMARY_COLS schema list for consistent CSV output."""
    return (
        leading
        + ["cluster_id", "tribe_label", "size", "n_respondents", "age", "health"]
        + [col for base in _CATEG_BASES for col in [base, f"{base}_pct", f"{base}_2", f"{base}_2_pct"]]
        + ["tribe_description", "reasoning"]
    )


# ── Per-batch helpers ─────────────────────────────────────────────────────────

def slice_and_rank(
    df_merged: pd.DataFrame,
    ladcd_val: str,
    group_val,
    max_pidps_per_group: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filter df_merged to one LA×group, aggregate by pidp, truncate to the
    top N by weight, then deduplicate by compact_profile.

    Returns (top, deduped).
    """
    mask = df_merged["ladcd"] == ladcd_val
    if group_val is not None:
        mask &= df_merged["group"] == group_val

    pidp_weights = (
        df_merged[mask]
        .groupby("pidp", sort=False)
        .agg(n=("n", "sum"), compact_profile=("compact_profile", "first"))
        .reset_index()
        .sort_values("n", ascending=False)
        .reset_index(drop=True)
    )
    top = pidp_weights.iloc[:max_pidps_per_group].copy()

    deduped = (
        top.groupby("compact_profile", sort=False)
        .agg(n=("n", "sum"))
        .reset_index()
        .sort_values("n", ascending=False)
        .reset_index(drop=True)
    )
    return top, deduped


def call_llm_with_retry(
    raw_chat_fn,
    profiles_weights: list,
    k: int,
    context: str,
    emp_group=None,
    retry_delay: int = 10,
    max_missing: int = 5,
) -> dict:
    """Call the model-specific raw_chat_fn with validation and up to 3 retries.

    raw_chat_fn(system: str, user: str) -> str  (raw JSON text from the model)

    Returns the parsed dict with keys: clusters, descriptions, assignments.
    """
    system_msg = SYSTEM_PROMPT.format(k=k)
    prompt     = build_user_prompt(profiles_weights, k, context, emp_group=emp_group)
    print(f"    {len(profiles_weights)} unique profiles, ~{len(prompt)//4:,} tokens", flush=True)
    print(f"\n── SYSTEM PROMPT ──\n{system_msg}", flush=True)
    print(f"\n── USER PROMPT ──\n{prompt}\n──────────────────\n", flush=True)

    for attempt in range(3):
        try:
            t0      = time.time()
            content = raw_chat_fn(system_msg, prompt)
            print(f"    {time.time()-t0:.1f}s", flush=True)
            parsed  = json.loads(content)

            k_actual = len(parsed["clusters"])
            if k_actual < 1 or k_actual > k:
                raise ValueError(f"Expected 1-{k} clusters, got {k_actual}")
            if len(parsed.get("descriptions", [])) != k_actual:
                raise ValueError(
                    f"Expected {k_actual} descriptions, got {len(parsed.get('descriptions', []))}"
                )

            n_assigned = len(parsed["assignments"])
            n_expected = len(profiles_weights)
            if n_assigned > n_expected or (n_expected - n_assigned) > max_missing:
                raise ValueError(f"Expected {n_expected} assignments, got {n_assigned}")
            if n_assigned < n_expected:
                print(
                    f"    Warning: {n_expected - n_assigned} missing assignment(s) — padding with 0",
                    flush=True,
                )
                parsed["assignments"] += [0] * (n_expected - n_assigned)

            parsed["clusters"]     = [sanitise_name(n) for n in parsed["clusters"]]
            parsed["descriptions"] = [sanitise_name(d) for d in parsed["descriptions"]]
            for name, desc in zip(parsed["clusters"], parsed["descriptions"]):
                print(f"    • {name}: {desc}", flush=True)
            return parsed

        except Exception as exc:
            print(f"    attempt {attempt+1} failed: {exc}", flush=True)
            traceback.print_exc()
            if attempt < 2:
                time.sleep(retry_delay)

    raise RuntimeError("LLM call failed after 3 attempts.")


def build_pidp_df(
    result: dict,
    deduped: pd.DataFrame,
    top: pd.DataFrame,
    ladcd_val: str,
    ladnm_val: str,
    group_val,
) -> pd.DataFrame:
    """Map LLM cluster assignments back to PIDPs in `top`.

    Returns a DataFrame with one row per PIDP.
    """
    cluster_names = result["clusters"]
    cluster_descs = result["descriptions"]

    profile_to_cluster = {
        row["compact_profile"]: min(int(result["assignments"][idx]), len(cluster_names) - 1)
        for idx, row in deduped.iterrows()
    }

    rows = []
    for _, row in top.iterrows():
        ci = profile_to_cluster.get(row["compact_profile"], 0)
        rows.append({
            "ladcd":             ladcd_val,
            "ladnm":             ladnm_val,
            "group":             group_val,
            "pidp":              int(row["pidp"]),
            "n_sipher_rows":     int(row["n"]),
            "cluster":           ci + 1,
            "tribe_label":       cluster_names[ci],
            "tribe_description": cluster_descs[ci],
        })
    return pd.DataFrame(rows)


def save_batch(
    la_df_pidp: pd.DataFrame,
    result: dict,
    df_features: pd.DataFrame,
    cs_module,
    pidp_out: Path,
    api_out: Path,
    ladcd_val: str,
    ladnm_val: str,
    group_val,
    hier_col: str | None,
    wave: str,
    summary_cols: list[str],
) -> None:
    """Append one LA×group batch to the PIDP CSV and the cluster-summary CSV."""
    pidp_write_header = not pidp_out.exists()
    la_df_pidp.to_csv(pidp_out, mode="a", header=pidp_write_header, index=False)
    print(f"  Saved {len(la_df_pidp)} PIDP assignments → {pidp_out}", flush=True)

    la_df_full = la_df_pidp.merge(df_features, on="pidp", how="left")
    la_df_full["ladnm"] = ladnm_val
    if hier_col:
        la_df_full["group"] = group_val

    la_summary = cs_module.make_cluster_summary(la_df_full, "cluster", wave=wave)

    name_map = la_df_pidp.drop_duplicates("cluster").set_index("cluster")["tribe_label"].to_dict()
    desc_map = la_df_pidp.drop_duplicates("cluster").set_index("cluster")["tribe_description"].to_dict()

    la_summary["tribe_label"]       = la_summary["cluster_id"].map(name_map).fillna(la_summary["tribe_label"])
    la_summary["tribe_description"] = la_summary["cluster_id"].map(desc_map)
    la_summary["reasoning"]         = result.get("reasoning", "")
    la_summary["ladcd"]             = ladcd_val
    la_summary["ladnm"]             = ladnm_val
    if hier_col:
        la_summary["group"] = group_val

    la_summary = la_summary.reindex(columns=summary_cols)

    write_header = not api_out.exists()
    la_summary.to_csv(api_out, mode="a", header=write_header, index=False)
    print(f"  Saved {len(la_summary)} cluster rows → {api_out}", flush=True)


# ── Final summary ─────────────────────────────────────────────────────────────

def print_final_summary(
    api_out: Path,
    pidp_out: Path,
    failed_pairs: list,
    leading: list[str],
    resolve_emp_label_fn,
) -> None:
    """Print totals and a preview table after all batches are complete."""
    df_summary  = pd.read_csv(api_out)
    df_pidp_all = pd.read_csv(pidp_out)
    print(f"\nDone. {len(df_summary)} total cluster rows in {api_out}")
    print(f"PIDP assignments: {len(df_pidp_all)} rows in {pidp_out}")

    if failed_pairs:
        print(f"\n{'='*60}")
        print(f"WARNING: {len(failed_pairs)} LA×group(s) failed and were skipped:")
        for ladcd_f, ladnm_f, group_f in failed_pairs:
            label_f = resolve_emp_label_fn(group_f) if group_f is not None else None
            print(f"  • {ladnm_f} / {label_f or group_f or '—'} ({ladcd_f})")
        print(f"{'='*60}")

    preview_cols = leading + ["cluster_id", "tribe_label", "tribe_description", "n_respondents", "size"]
    print(df_summary[[c for c in preview_cols if c in df_summary.columns]].to_string(index=False))
