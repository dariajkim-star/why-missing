"""Crash-safe output - gate 3 of the lineage contract's implementation ladder.

A half-written named list that survives a crash is a lie with a filename:
the reader assumes 50 rows means 50 judged, when it means "crashed at 50".
So (a) the final file appears only via atomic replace after a complete write,
and (b) the completion meta records ROWS EXAMINED separately from rows
written - "examined 100, wrote 50 verdicts" and "examined 50, crashed" must
be distinguishable (Sally clause).
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def atomic_write_with_meta(
    path: Path,
    lines: list[str],
    rows_examined: int,
    _fail_before_commit: bool = False,  # test hook: simulated crash
) -> None:
    """Write `lines` to `path` atomically; sidecar meta records completion."""
    if rows_examined < len(lines):
        raise ValueError(
            f"rows_examined ({rows_examined}) < rows written ({len(lines)}): "
            f"an output cannot contain rows nobody examined"
        )
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    if _fail_before_commit:
        raise RuntimeError("simulated crash before commit")
    os.replace(tmp, path)
    meta = {"rows_written": len(lines), "rows_examined": rows_examined, "complete": True}
    path.with_suffix(path.suffix + ".meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8")
