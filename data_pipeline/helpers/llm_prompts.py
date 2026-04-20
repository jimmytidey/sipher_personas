"""
Shared prompt text and utilities for LLM-based local-area clustering notebooks
(14_llm_cluster_LA_gemini, 15_llm_cluster_LA_claude, …).

Import with:
    from data_pipeline.helpers.llm_prompts import (
        CODEBOOK_STR, SYSTEM_PROMPT, sanitise_name, build_user_prompt,
        resolve_emp_label, allocate_clusters,
    )
"""

# Maps numeric jbstat codes (as stored in the hierarchical-cluster column) to
# human-readable employment labels used in prompt context.
EMP_LABELS: dict[int, str] = {
    1: "Self-employed",
    2: "Employed",
    3: "Unemployed",
    4: "Retired",
    5: "On leave / maternity",
    6: "Family care",
    7: "Student / in training",
    8: "Long-term sick or disabled",
    97: "Other employment status",
}


def resolve_emp_label(group) -> str | None:
    """Return a human-readable employment label for a numeric jbstat group value.

    Accepts int, float, or string representations (e.g. 5, 5.0, "5.0").
    Returns None if group is None / empty / unrecognised.
    """
    if group is None:
        return None
    try:
        key = int(float(group))
        return EMP_LABELS.get(key)
    except (TypeError, ValueError):
        s = str(group).strip()
        return s if s and s.lower() not in ("none", "") else None


def allocate_clusters(
    group_populations: dict,
    total_clusters: int,
    min_per_group: int = 1,
) -> dict:
    """
    Proportionally allocate ``total_clusters`` across groups weighted by population.

    Uses the largest-remainder method so allocations sum to exactly ``total_clusters``.
    Every group receives at least ``min_per_group`` clusters.

    Args:
        group_populations: {group_key: population_count} mapping.
        total_clusters:    total cluster budget to distribute.
        min_per_group:     minimum clusters per group (default 1).

    Returns:
        {group_key: n_clusters} dict with the same keys as ``group_populations``.
    """
    groups = list(group_populations.keys())
    total_pop = sum(group_populations.values())

    if not groups:
        return {}
    if total_pop == 0:
        return {g: min_per_group for g in groups}

    exact = {g: total_clusters * group_populations[g] / total_pop for g in groups}
    result = {g: max(min_per_group, int(exact[g])) for g in groups}

    remaining = total_clusters - sum(result.values())
    if remaining > 0:
        # Award leftover slots to groups with largest fractional remainders
        order = sorted(groups, key=lambda g: exact[g] - int(exact[g]), reverse=True)
        for g in order[:remaining]:
            result[g] += 1
    # If remaining < 0 the minimum constraints forced over-allocation — accept it.

    return result


CODEBOOK_STR = """\
VARIABLE CODEBOOK — each profile row: age|sex|eth|edu|emp|mar|ten|hh|health  (? = unknown)
  age:    years (numeric)
  sex:    1=Male 2=Female
  eth:    1=White British  2=White Irish  4=White Other  5=Mixed White/Black Carib  7=Mixed White/Asian  8=Mixed Other  9=Asian Indian  10=Asian Pakistani  11=Asian Bangladeshi  12=Asian Chinese  14=Black Caribbean  15=Black African  17=Arab  97=Other
  edu:    1=Degree  2=Other higher  3=A-level  4=GCSE  5=Other qual  9=No qual
  emp:    1=Self-employed  2=Employed  3=Unemployed  4=Retired  5=Maternity  6=Family care  7=Student  8=LT sick/disabled  97=Other
  mar:    1=Married  2=Cohabiting  3=Widowed  4=Divorced  5=Separated  6=Single
  ten:    1=Owned outright  2=Mortgage  3=Council rent  4=Housing assoc  5=Employer rent  6=Private unfurn  7=Private furn
  hh:     1=Solo M 65+  2=Solo F 60+  3=Solo adult  4=Single parent 1c  5=Single parent 2+c  6=Couple no child  8=Couple (pensionable age)  10=Couple+1c  11=Couple+2c  12=Couple+3+c  16=2 adults  17=2 adults (pensionable)  18=2 adults+child  19=3+ couple  22=3+ no couple
  health: 1=Excellent  2=Very good  3=Good  4=Fair  5=Poor"""

# System prompt template — call .format(k=<n_clusters>) before sending.
SYSTEM_PROMPT = (
    "You are a social researcher analysing UK survey respondents who represent a "
    "local population. Each profile is encoded as numeric codes (see codebook in the user message). "
    "Each profile is followed by a weight — how many people in that local area that respondent represents. "
    "Read all profiles and group them into up to {k} meaningful, distinct clusters, "
    "weighting by population weight. "
    "Use fewer clusters if the data does not clearly support {k} — every cluster must be "
    "genuinely distinct; do not split a group arbitrarily just to reach the maximum. "
    "Give each cluster a vivid, specific name — 'Young Urban Renters' beats 'Group A'. "
    "Also write a 1–2 sentence plain-English description of who is in each cluster and what defines them. "
    "Cluster names and descriptions must be plain text: no quotes, commas within names, or line breaks.\n\n"
    "IMPORTANT: Your response must be a raw JSON object only. "
    "Do NOT wrap it in code fences (no ```json or ```). "
    "Do NOT include any explanation or text outside the JSON object."
)

# Hierarchical-clustering note inserted into the user prompt when a jbstat group
# is provided.  Placeholder {emp_label} and {k} are filled by build_user_prompt.
_HIER_NOTE = (
    "HIERARCHICAL CLUSTERING CONTEXT: A two-stage clustering approach is being used. "
    "In the first stage, the full local population was divided into broad employment-status "
    "groups using the 'emp' field in the codebook. The profiles below have already been "
    "filtered to a single employment group: '{emp_label}'. "
    "Your task is the second stage — find up to {k} meaningful sub-clusters *within* this "
    "employment group by focusing on other dimensions such as age, household type, "
    "housing tenure, education, ethnicity, marital status, and health. "
    "Use fewer clusters if the data does not clearly support {k} distinct groups. "
    "Do NOT name or describe clusters using employment status — that dimension is fixed "
    "and identical for every respondent in this batch."
)


def sanitise_name(name: str) -> str:
    """Strip whitespace and remove characters that would corrupt a CSV cell."""
    return (
        str(name)
        .strip()
        .replace("\n", " ")
        .replace("\r", "")
        .replace('"', "'")
    )


def build_user_prompt(
    profiles_weights: list,
    k: int,
    context: str,
    emp_group=None,
) -> str:
    """
    Build the user-turn prompt string for the clustering task.

    Args:
        profiles_weights: list of (compact_profile_str, weight_int) tuples,
                          ordered highest-weight first.
        k:               number of clusters requested.
        context:         short free-text description of the LA / group being processed.
        emp_group:       numeric jbstat group value (int, float, or string like "5.0"),
                         or None if not using hierarchical clustering.  When provided,
                         the prompt will explain the two-stage hierarchical setup.

    Returns:
        The full user prompt string ready to send to any LLM.
    """
    lines = "\n".join(
        f"{i}. [weight:{w}]  {p}"
        for i, (p, w) in enumerate(profiles_weights)
    )

    hier_block = ""
    if emp_group is not None:
        emp_label = resolve_emp_label(emp_group) or str(emp_group)
        hier_block = f"\n{_HIER_NOTE.format(emp_label=emp_label, k=k)}\n"

    return (
        f"Context: {context}\n"
        f"{hier_block}\n"
        f"{CODEBOOK_STR}\n\n"
        f"Below are {len(profiles_weights)} respondent profiles "
        f"(numbered 0–{len(profiles_weights) - 1}):\n\n{lines}\n\n"
        f"Return a raw JSON object with exactly these four keys — no code fences, no extra text:\n"
        f'  "reasoning": a short paragraph explaining the overall rationale for how the respondents were segmented '
        f'(which dimensions drove the split and why they were the most meaningful)\n'
        f'  "clusters": array of 1 to {k} cluster name strings\n'
        f'  "descriptions": array of the same length as "clusters" (one plain-English description per cluster, same order)\n'
        f'  "assignments": array of exactly {len(profiles_weights)} integers, each in the range 0 to len(clusters)-1, '
        f"one per profile in the same order."
    )
