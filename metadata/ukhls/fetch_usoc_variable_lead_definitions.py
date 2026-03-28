#!/usr/bin/env python3
"""Fetch Understanding Society mainstage variable blurbs (p.lead) and merge into CSV.

Source: https://www.understandingsociety.ac.uk/documentation/mainstage/variables/{variable}

Requires: beautifulsoup4. Run with network access.

  venv/bin/python data/0_raw/ukhls/fetch_usoc_variable_lead_definitions.py

Reads:  data/0_raw/ukhls/xwavedat_nonnegative_pct.csv
Writes: same path (adds / overwrites columns: documentation_url, definition_lead)

Uses a JSON cache alongside the CSV so re-runs only fetch missing variables.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd
from bs4 import BeautifulSoup

# .../data/0_raw/ukhls/this_file.py → repo root is parents[3]
REPO = Path(__file__).resolve().parents[3]
CSV_PATH = REPO / "data" / "0_raw" / "ukhls" / "xwavedat_nonnegative_pct.csv"
CACHE_PATH = REPO / "data" / "0_raw" / "ukhls" / ".usoc_variable_lead_cache.json"

BASE = "https://www.understandingsociety.ac.uk/documentation/mainstage/variables"
USER_AGENT = "Mozilla/5.0 (compatible; archetypes-local-tool/1.0; +https://github.com/)"
REQUEST_PAUSE_SEC = 0.35
TIMEOUT_SEC = 45


def fetch_lead(variable: str) -> tuple[str | None, str | None]:
    """Return (definition_text, error_message)."""
    url = f"{BASE}/{variable}"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=TIMEOUT_SEC) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        return None, f"HTTP {e.code}"
    except URLError as e:
        return None, f"URL {e.reason!r}"
    soup = BeautifulSoup(html, "html.parser")
    p = soup.select_one("p.lead")
    if not p:
        return None, "no p.lead"
    text = p.get_text(" ", strip=True)
    return (text if text else None), None


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache, indent=0, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    df = pd.read_csv(CSV_PATH)
    for c in ("documentation_url", "definition_lead", "definition_fetch_error"):
        if c in df.columns:
            df = df.drop(columns=[c])
    cache = load_cache()
    variables = df["variable"].astype(str).str.strip().tolist()

    for i, var in enumerate(variables):
        key = var
        if key in cache and isinstance(cache[key], dict) and "definition_lead" in cache[key]:
            continue
        lead, err = fetch_lead(var)
        cache[key] = {
            "definition_lead": lead,
            "fetch_error": err,
            "documentation_url": f"{BASE}/{var}",
        }
        save_cache(cache)
        if (i + 1) % 5 == 0 or i == 0:
            print(f"[{i+1}/{len(variables)}] {var!r} -> {lead[:60] + '...' if lead and len(lead) > 60 else lead!r} {err or ''}")
        time.sleep(REQUEST_PAUSE_SEC)

    df["documentation_url"] = [f"{BASE}/{v}" for v in variables]
    df["definition_lead"] = [cache.get(v, {}).get("definition_lead") for v in variables]
    errs = [cache.get(v, {}).get("fetch_error") for v in variables]
    if any(errs):
        df["definition_fetch_error"] = errs

    df.to_csv(CSV_PATH, index=False)
    print(f"Updated {CSV_PATH} ({len(df)} rows)")
    n_ok = df["definition_lead"].notna().sum()
    print(f"definition_lead non-empty: {n_ok} / {len(df)}")


if __name__ == "__main__":
    main()
