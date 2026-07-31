"""Peer cell construction - contract 6: SIC4, n >= 10, SIC3 promotion, else NO VERDICT.

A forced cell is worse than no cell: four peers is gossip (party verdict
2026-07-29). NO_VERDICT is a first-class outcome, never an exception swallowed
upstream.
"""
from __future__ import annotations

from dataclasses import dataclass

from adjudicator.config import PEER_MIN_CELL


@dataclass(frozen=True)
class PeerCell:
    level: str  # "SIC4" | "SIC3"
    sic_prefix: str
    members: tuple


def build_cell(sic4_members: list, sic3_members: list, sic: str,
               min_n: int = PEER_MIN_CELL) -> PeerCell | None:
    """Return the cell, or None (= no verdict). Never a padded cell."""
    if len(sic4_members) >= min_n:
        return PeerCell("SIC4", sic[:4], tuple(sic4_members))
    if len(sic3_members) >= min_n:
        return PeerCell("SIC3", sic[:3], tuple(sic3_members))
    return None
