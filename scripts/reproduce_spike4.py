"""M1 - reproduce spike 4's intangibles census with committed code.

Network work lives HERE, not in tests. This writes a snapshot artifact plus a
lineage meta; `tests/test_golden_spike4.py` then compares that snapshot to the
committed golden offline and deterministically.

Run:  .venv/Scripts/python.exe scripts/reproduce_spike4.py
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adjudicator import concepts, residual, sec  # noqa: E402
from adjudicator.freshness import build_meta, save_meta  # noqa: E402

QUARTERS = ("2024q3", "2024q4", "2025q1", "2025q2")  # spike 4 window
CACHE = Path.home() / ".cache" / "why-missing" / "notes"
OUT = Path(__file__).resolve().parents[1] / "docs" / "data" / "spike4-census-reproduced.json"


def main() -> int:
    concept = concepts.resolve("finite_lived_intangibles_net")
    tags = residual.tags_of_interest(concept)
    all_filings, provenance = [], {}
    for q in QUARTERS:
        data = sec.load_quarter(q, tags, CACHE)
        found = residual.find_residuals(data.sub, data.num, concept, q)
        all_filings.extend(found)
        provenance[q] = list(data.zip_names)
        print(f"{q}: 10-K filings {len(data.sub[data.sub['form'] == '10-K'])}, "
              f"residual filings {len(found)}", flush=True)

    companies = residual.one_per_company(all_filings)
    print(f"\nTOTAL residual filings {len(all_filings)} across {len(companies)} companies")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "concept": concept.key,
        "window": list(QUARTERS),
        "archives_used": provenance,
        "residual_filings": len(all_filings),
        "companies": [asdict(f) for f in companies],
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    save_meta(build_meta(OUT.name, {q: json.dumps(provenance[q]).encode() for q in QUARTERS}),
              OUT.with_suffix(".meta.json"))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
