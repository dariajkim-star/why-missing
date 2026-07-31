"""Data lineage & integrity contract, clause 1 - row identity (contract 9).

Every result row must carry a validated CIK-accession pair. And a fetch that
FAILED is never evidence of absence: 404 (the authority says "no such
document") and a network/server failure are different facts, and only the
first may ever feed an absence judgement. Spike 6 run 1 confused the two
(a URL typo logged every quarter as "dataset unavailable") - the
infrastructure edition of absence-is-not-omission.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

_ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")


@dataclass(frozen=True)
class RowIdentity:
    cik: int
    accession: str

    def __post_init__(self):
        if not isinstance(self.cik, int) or self.cik <= 0:
            raise ValueError(f"cik must be a positive int, got {self.cik!r}")
        if not _ACCESSION_RE.match(self.accession):
            raise ValueError(
                f"accession {self.accession!r} is not a canonical SEC accession "
                f"(NNNNNNNNNN-NN-NNNNNN). Identity comes from the submissions "
                f"API, never from a search index."
            )


class FetchOutcome(Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"      # authoritative 404 - may inform absence
    FETCH_FAILED = "fetch_failed"  # network/5xx/timeout - may NOT inform absence


def classify_http(status: int | None) -> FetchOutcome:
    """None means the request itself failed (timeout, DNS, refused)."""
    if status is None:
        return FetchOutcome.FETCH_FAILED
    if status == 200:
        return FetchOutcome.FOUND
    if status == 404:
        return FetchOutcome.NOT_FOUND
    return FetchOutcome.FETCH_FAILED


class AccessFailureIsNotAbsence(RuntimeError):
    pass


def require_observable(outcome: FetchOutcome) -> FetchOutcome:
    """Gate before any absence logic: a failed fetch cannot testify."""
    if outcome is FetchOutcome.FETCH_FAILED:
        raise AccessFailureIsNotAbsence(
            "the fetch FAILED; failure to reach a source is not evidence that "
            "the value is absent. Retry or record 'unmeasured' - never 'absent'."
        )
    return outcome
