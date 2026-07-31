"""SEC acquisition - contract 8, and the only module that touches the network.

Two rules the rehearsal paid for:

  1. The NOTES data sets, not the face-financials bulk. Footnote-level tags live
     only there (OperatingLeaseLiability coverage 6.0% face vs 79.4% notes), and
     reading face-only would name ~94% of filers as omitting what they disclosed.
  2. Quarterly zips through 2025q2, MONTHLY zips from 2025q3 onward. A naive
     quarter loop silently loses a year of data at that boundary (T1 trap).

Every fetch is classified through `identity.classify_http`: a 404 is the
authority saying "no such file", a timeout is us failing. Only the first may
ever inform an absence judgement.
"""
from __future__ import annotations

import io
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

from adjudicator.config import SEC_RATE_SLEEP_SECONDS, SEC_USER_AGENT
from adjudicator.identity import FetchOutcome, classify_http, require_observable

NOTES_BASE = "https://www.sec.gov/files/dera/data/financial-statement-notes-data-sets"
# source: measured 2026-07-31 - quarterly zips exist through 2025q2; from 2025q3
# the publication switches to monthly (`YYYY_MM_notes.zip`).
MONTHLY_FROM = (2025, 3)


class SourceUnavailable(RuntimeError):
    """The authority says the file does not exist (404). Distinct from a failure."""


@dataclass(frozen=True)
class QuarterData:
    quarter: str
    sub: pd.DataFrame
    num: pd.DataFrame
    zip_names: tuple[str, ...]  # provenance: which archives this was built from


def _get(url: str, cache_dir: Path, name: str) -> Path | None:
    """Download to cache. Returns None on an authoritative 404; raises on failure."""
    dest = cache_dir / name
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    marker = cache_dir / (name + ".notfound")
    if marker.exists():
        return None
    try:
        r = requests.get(url, headers={"User-Agent": SEC_USER_AGENT}, timeout=900)
        status = r.status_code
    except requests.RequestException:
        status = None
    time.sleep(SEC_RATE_SLEEP_SECONDS)
    outcome = classify_http(status)
    if outcome is FetchOutcome.NOT_FOUND:
        marker.write_text("404", encoding="utf-8")  # cache the AUTHORITATIVE fact only
        return None
    require_observable(outcome)  # raises AccessFailureIsNotAbsence on failure
    dest.write_bytes(r.content)
    return dest


def _read_zip(path: Path, tags: frozenset[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    zf = zipfile.ZipFile(path)
    names = {n.lower(): n for n in zf.namelist()}
    sub = pd.read_csv(io.BytesIO(zf.read(names.get("sub.tsv") or names["sub.txt"])),
                      sep="\t", dtype=str, on_bad_lines="skip", low_memory=False,
                      usecols=["adsh", "cik", "name", "sic", "form", "period", "fy", "fp"])
    parts = []
    for chunk in pd.read_csv(
            io.BytesIO(zf.read(names.get("num.tsv") or names["num.txt"])),
            sep="\t", dtype=str, on_bad_lines="skip", low_memory=False, chunksize=1_000_000,
            usecols=["adsh", "tag", "coreg", "ddate", "qtrs", "uom", "value"]):
        parts.append(chunk[chunk["tag"].isin(tags)])
    num = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(
        columns=["adsh", "tag", "coreg", "ddate", "qtrs", "uom", "value"])
    return sub, num


def archive_names(quarter: str) -> list[str]:
    """The archive file names that make up a quarter (T1 monthly-switch trap)."""
    year, q = int(quarter[:4]), int(quarter[-1])
    if (year, q) < MONTHLY_FROM:
        return [f"{quarter}_notes.zip"]
    return [f"{year}_{m:02d}_notes.zip" for m in range((q - 1) * 3 + 1, q * 3 + 1)]


def load_quarter(quarter: str, tags: frozenset[str], cache_dir: Path) -> QuarterData:
    """Load one quarter of NOTES data, transparently spanning monthly archives."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    subs, nums, used = [], [], []
    for name in archive_names(quarter):
        path = _get(f"{NOTES_BASE}/{name}", cache_dir, name)
        if path is None:
            continue
        s, n = _read_zip(path, tags)
        subs.append(s)
        nums.append(n)
        used.append(name)
    if not subs:
        raise SourceUnavailable(
            f"no notes archive exists for {quarter} (tried {archive_names(quarter)}); "
            f"this is a 404 from SEC, not a fetch failure"
        )
    return QuarterData(quarter, pd.concat(subs, ignore_index=True),
                       pd.concat(nums, ignore_index=True), tuple(used))
