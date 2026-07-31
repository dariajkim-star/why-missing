"""Self-check rule - contract 3: if big companies top your suspicion ranking,
suspect yourself first.

Fired three-for-three in the rehearsal (LabCorp/FIS/ADM; Synchrony/Progressive/
Aflac/PNC; spike-4 P4). Large audited filers do not forget to disclose - a
large filer at the top of a gap ranking almost always means OUR tag list or
absence definition is wrong, not their disclosure.
"""
from __future__ import annotations

# source: judgement convention distilled from three incidents; deliberately a
# coarse multiple, not a fitted value.
LARGE_VS_MEDIAN_FACTOR = 50.0


def large_company_alarm(
    top_assets: list[float],
    population_median_assets: float,
    factor: float = LARGE_VS_MEDIAN_FACTOR,
) -> list[int]:
    """Indices (into the top-ranked list) whose size demands self-suspicion.

    Returns positions, not a boolean - the caller must name WHICH entries
    triggered the alarm in its report, or the warning is unactionable.
    """
    if population_median_assets <= 0:
        raise ValueError("population median assets must be positive")
    return [i for i, a in enumerate(top_assets) if a > factor * population_median_assets]
