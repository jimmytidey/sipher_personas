# data_pipeline/helpers/derive_variables.py
#
# Composite scores used by KEEP/5a_derive_variables.ipynb: digital_use, service_use,
# derived_work_status.
# Maps UKHLS raw codes to 0–1 component scores, then averages (ignoring missing components).

from __future__ import annotations

import numpy as np
import pandas as pd

# Standard UKHLS missing / non-response codes (treated as missing for scoring)
_INVALID_SENTINELS: frozenset[float] = frozenset({-9.0, -8.0, -7.0, -2.0, -1.0})


def _numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _mask_invalid(s: pd.Series) -> pd.Series:
    v = _numeric(s)
    return v.where(~v.isin(_INVALID_SENTINELS))


def _score_netpusenew(s: pd.Series) -> pd.Series:
    """Internet use frequency — higher score = more engagement."""
    v = _mask_invalid(s)
    m = {
        1.0: 1.0,
        2.0: 0.95,
        3.0: 0.88,
        4.0: 0.75,
        5.0: 0.58,
        6.0: 0.42,
        7.0: 0.25,
        8.0: 0.0,
        9.0: 0.0,
    }
    return v.map(m)


def _score_yes_no(s: pd.Series) -> pd.Series:
    v = _mask_invalid(s)
    return v.map({1.0: 1.0, 2.0: 0.0})


def _score_freq_internet_6(s: pd.Series) -> pd.Series:
    """browse/email/social/streaming etc.: 1 = every day … 6 = never."""
    v = _mask_invalid(s)
    m = {
        1.0: 1.0,
        2.0: 0.83,
        3.0: 0.67,
        4.0: 0.5,
        5.0: 0.33,
        6.0: 0.0,
    }
    return v.map(m)


def _score_hl2gp(s: pd.Series) -> pd.Series:
    """GP visits in last 12m: 0 none → 4+ frequent."""
    v = _mask_invalid(s)
    m = {
        0.0: 0.0,
        1.0: 0.25,
        2.0: 0.5,
        3.0: 0.75,
        4.0: 1.0,
    }
    return v.map(m)


def _score_mentioned(s: pd.Series) -> pd.Series:
    """servuse / othben / benbase: 0 not mentioned, 1 mentioned."""
    v = _mask_invalid(s)
    return v.map({0.0: 0.0, 1.0: 1.0})


def _score_fimnsben(s: pd.Series, clip: float = 15_000.0) -> pd.Series:
    """Social benefit income — 0–1 after floor 0 and upper clip."""
    v = _numeric(s)
    v = v.where(~v.isin(_INVALID_SENTINELS))
    v = v.clip(lower=0.0, upper=clip)
    return (v / clip).astype(float)


def compute_digital_use(df: pd.DataFrame, wave: str = "o") -> pd.Series:
    """Mean of mapped 0–1 scores over digital columns present in *df*."""
    p = f"{wave}_"
    specs: list[tuple[str, callable]] = [
        (f"{p}netpusenew", _score_netpusenew),
        (f"{p}laptop", _score_yes_no),
        (f"{p}smtphone", _score_yes_no),
    ]
    for base in (
        "browse",
        "email",
        "smlook",
        "smpost",
        "onlinebuy",
        "onlinebank",
        "streaming",
    ):
        specs.append((f"{p}{base}", _score_freq_internet_6))

    parts: list[pd.Series] = []
    for col, fn in specs:
        if col in df.columns:
            parts.append(fn(df[col]))
        else:
            parts.append(pd.Series(np.nan, index=df.index, dtype=float))

    if not parts:
        return pd.Series(0.0, index=df.index)

    mat = pd.concat(parts, axis=1)
    out = mat.mean(axis=1, skipna=True)
    return out.fillna(0.0).clip(0.0, 1.0).astype(np.float32)


def compute_service_use(df: pd.DataFrame, wave: str = "o") -> pd.Series:
    """Mean of service / benefit intensity components (each 0–1), equal weight."""
    p = f"{wave}_"
    specs: list[tuple[str, callable]] = [
        (f"{p}hl2gp", _score_hl2gp),
        (f"{p}servuse2", _score_mentioned),
        (f"{p}servuse10", _score_mentioned),
        (f"{p}benbase4", _score_mentioned),
        (f"{p}othben6", _score_mentioned),
        (f"{p}othben8", _score_mentioned),
        (f"{p}othben1", _score_mentioned),
        (f"{p}othben2", _score_mentioned),
        (f"{p}fimnsben_dv", _score_fimnsben),
    ]

    parts: list[pd.Series] = []
    for col, fn in specs:
        if col in df.columns:
            parts.append(fn(df[col]))
        else:
            parts.append(pd.Series(np.nan, index=df.index, dtype=float))

    mat = pd.concat(parts, axis=1)
    out = mat.mean(axis=1, skipna=True)
    return out.fillna(0.0).clip(0.0, 1.0).astype(np.float32)


# Raw UKHLS jbstat: 1 = self-employed, 2 = paid employment (ft/pt) — see config_variables_sipher_weighted.
_PAID_OR_SELF_EMPLOYED: frozenset[float] = frozenset({1.0, 2.0})


def compute_derived_work_status(df: pd.DataFrame, wave: str = "o") -> pd.Series:
    """Copy NS-SEC (variable ``jbnssec8_dv``) only for self-employed or paid employment; else NaN.

    Reads the wave-prefixed column ``{wave}_jbnssec8_dv`` (e.g. ``o_jbnssec8_dv`` when *wave* is
    ``"o"``). Config uses the base name ``jbnssec8_dv``; the ``o_`` prefix is the UKHLS wave letter
    for the indresp extract, same as all other pipeline columns.

    If ``{wave}_jbstat_raw`` is present (from backfill, pre–feature-eng recode), uses raw codes 1
    and 2. Otherwise falls back to recoded ``{wave}_jbstat == 1.0`` (Employed group).
    """
    p = f"{wave}_"
    raw_col = f"{p}jbstat_raw"
    rec_col = f"{p}jbstat"
    nsec_col = f"{p}jbnssec8_dv"

    nsec = (
        pd.to_numeric(df[nsec_col], errors="coerce")
        if nsec_col in df.columns
        else pd.Series(np.nan, index=df.index)
    )
    out = pd.Series(np.nan, index=df.index, dtype=float)

    if raw_col in df.columns:
        jb = pd.to_numeric(df[raw_col], errors="coerce")
        mask = jb.isin(_PAID_OR_SELF_EMPLOYED)
    elif rec_col in df.columns:
        jb = pd.to_numeric(df[rec_col], errors="coerce")
        mask = jb == 1.0
    else:
        return out.astype(np.float32)

    out.loc[mask] = nsec.loc[mask]
    return out.astype(np.float32)
