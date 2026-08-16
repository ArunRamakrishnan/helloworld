"""Reusable tiered-scoring evaluator shared by every scoring agent.

Replaces the repeated `if value >= a: return 10 elif value >= b: return 8 ...`
ladders that used to be hardcoded per-agent. Tiers are now data (loaded from
config/default.yaml) instead of code, so retuning a threshold is a config edit.
"""
from typing import List, Optional, Sequence, Tuple

Tier = Tuple[float, float]


def tiered_score(
    value: Optional[float],
    tiers: Sequence[Tier],
    no_match: float = 0.0,
    if_none: float = 0.0,
    mode: str = "gte",
) -> float:
    """
    Evaluates `value` against an ordered list of (threshold, score) tiers.

    mode="gte" (higher-is-better ladders, e.g. ROE): tiers must be sorted with the
        highest threshold first; returns the score of the first tier where
        value >= threshold.
    mode="lte" (lower-is-better ladders, e.g. PE, debt/equity): tiers must be sorted
        with the lowest threshold first; returns the score of the first tier where
        value <= threshold.

    Returns `if_none` when value is None, `no_match` when no tier matches.
    """
    if value is None:
        return if_none
    if mode == "gte":
        for threshold, score in tiers:
            if value >= threshold:
                return score
    elif mode == "lte":
        for threshold, score in tiers:
            if value <= threshold:
                return score
    else:
        raise ValueError(f"Unknown tiered_score mode: {mode!r}")
    return no_match


def weighted_average(scores: Sequence[Tuple[float, float]]) -> float:
    """Given a list of (score, weight) pairs, returns the weighted sum."""
    return sum(score * weight for score, weight in scores)
