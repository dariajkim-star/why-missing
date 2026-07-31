"""Data lineage & integrity contract, clause 2 - freshness (contract 9).

The pre-committed pass bar (party amendment, daria-ratified 2026-07-31):
if an upstream artifact changes and a downstream artifact passes without
recomputation, a test MUST fail. A timestamp in a sidecar is exactly the
level that transitive staleness walked through in the rehearsal - so the
check here compares content fingerprints along the chain, not clocks.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


def fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class LineageMeta:
    """What a derived artifact records about the sources it was built from."""
    output_name: str
    input_fingerprints: dict[str, str]  # source name -> sha256 at build time


def build_meta(output_name: str, inputs: dict[str, bytes]) -> LineageMeta:
    return LineageMeta(output_name, {k: fingerprint(v) for k, v in inputs.items()})


def is_stale(meta: LineageMeta, current_inputs: dict[str, bytes]) -> list[str]:
    """Names of inputs that changed since the artifact was built.

    A source missing from `current_inputs` is reported stale too - a vanished
    input is a change, not a pass.
    """
    stale = []
    for name, recorded in meta.input_fingerprints.items():
        now = current_inputs.get(name)
        if now is None or fingerprint(now) != recorded:
            stale.append(name)
    return stale


def save_meta(meta: LineageMeta, path: Path) -> None:
    path.write_text(json.dumps(
        {"output": meta.output_name, "inputs": meta.input_fingerprints},
        indent=2), encoding="utf-8")


def load_meta(path: Path) -> LineageMeta:
    d = json.loads(path.read_text(encoding="utf-8"))
    return LineageMeta(d["output"], d["inputs"])
