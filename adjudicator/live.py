"""Single-company acquisition for the interactive path (M3).

The bulk quarterly archives are the right source for a POPULATION; they are the
wrong source for one company on demand - hundreds of megabytes for a question
that should take seconds.

`companyfacts` is that door, under a condition. Spike 6 banned it because it
merges amendments, so a restated filer looks correctly tagged in hindsight.
Every fact in it, however, carries the `accn` of the filing that reported it,
so filtering to ONE accession restores point-in-time faithfulness. That filter
is not optional: there is deliberately no code path here that reads
companyfacts without pinning an accession.

Known blind spot, surfaced in every candidate verdict (never buried in a doc):
companyfacts carries only undimensioned facts. A filer who tags intangibles by
class (iWallet, EVA Live in the spike 4 census) discloses the value in a place
this door cannot see.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import requests

from adjudicator.config import SEC_RATE_SLEEP_SECONDS, SEC_USER_AGENT
from adjudicator.identity import RowIdentity, classify_http, require_observable

_HEADERS = {"User-Agent": SEC_USER_AGENT}


class NotFound(LookupError):
    pass


def _json(url: str):
    try:
        r = requests.get(url, headers=_HEADERS, timeout=60)
        status = r.status_code
    except requests.RequestException:
        status = None
    time.sleep(SEC_RATE_SLEEP_SECONDS)
    from adjudicator.identity import FetchOutcome
    outcome = require_observable(classify_http(status))
    if outcome is FetchOutcome.NOT_FOUND:
        raise NotFound(url)
    return r.json()


def resolve_company(query: str) -> tuple[int, str]:
    """Accept a CIK, a ticker, or a name fragment. Returns (cik, name)."""
    q = query.strip()
    if q.isdigit():
        data = _json(f"https://data.sec.gov/submissions/CIK{int(q):010d}.json")
        return int(q), data.get("name", "")
    table = _json("https://www.sec.gov/files/company_tickers.json")
    rows = list(table.values())
    for row in rows:  # exact ticker first
        if row["ticker"].upper() == q.upper():
            return int(row["cik_str"]), row["title"]
    hits = [r for r in rows if q.upper() in r["title"].upper()]
    if len(hits) == 1:
        return int(hits[0]["cik_str"]), hits[0]["title"]
    if not hits:
        raise NotFound(f"no company matches {query!r}")
    raise LookupError(
        f"{query!r} matches {len(hits)} companies; be specific: "
        + ", ".join(f"{h['ticker']}={h['title']}" for h in hits[:5])
    )


@dataclass(frozen=True)
class FilingRef:
    identity: RowIdentity
    company: str
    sic: str
    filed: str
    period: str
    form: str


def latest_annual(cik: int) -> FilingRef:
    """The most recent 10-K. Identity comes from the submissions API (authoritative)."""
    data = _json(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    recent = data.get("filings", {}).get("recent", {})
    for i, form in enumerate(recent.get("form", [])):
        if form == "10-K":
            return FilingRef(
                identity=RowIdentity(cik=cik, accession=recent["accessionNumber"][i]),
                company=data.get("name", ""), sic=str(data.get("sic", "") or ""),
                filed=recent["filingDate"][i], period=recent["reportDate"][i], form=form,
            )
    raise NotFound(f"CIK {cik} has filed no 10-K")


def tags_reported_in(filing: FilingRef, candidate_tags: frozenset[str]) -> frozenset[str]:
    """Which of `candidate_tags` THIS filing tagged (point-in-time, accn-pinned)."""
    facts = _json(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{filing.identity.cik:010d}.json"
    ).get("facts", {}).get("us-gaap", {})
    accession = filing.identity.accession
    found = set()
    for tag in candidate_tags:
        entry = facts.get(tag)
        if not entry:
            continue
        for unit_rows in entry.get("units", {}).values():
            if any(row.get("accn") == accession for row in unit_rows):
                found.add(tag)
                break
    return frozenset(found)
