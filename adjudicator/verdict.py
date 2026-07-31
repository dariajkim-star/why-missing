"""The six-form verdict - the product's voice (contracts 1, 2; MVP M4).

Hard rule, enforced here and pinned by a test: the system CANNOT output
"omission confirmed" (or its Korean form). Detection power was measured as
unverifiable (spike 5, X1 unmet), so form 1 is forever a CANDIDATE requiring
human confirmation. A rendering path that could emit certainty would be the
permanent caveat's product-level violation.

Every verdict carries a non-empty evidence line quoting OBSERVED values -
an exclusion-style line without evidence is a blacklist, not a judgement.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from adjudicator.concepts import Concept


class Form(Enum):
    CANDIDATE_OMISSION = 1   # absent everywhere we can see - HUMAN CONFIRMATION REQUIRED
    REPORTED_ELSEWHERE = 2
    DERIVABLE_SUBTOTAL = 3
    NOT_APPLICABLE = 4
    LEGITIMATE_ZERO = 5      # never produced at runtime - flow concepts are rejected at input
    INDUSTRY_HOMONYM = 6
    PRESENT = 0              # not a gap: the standard tag is right where it belongs
    NO_VERDICT = -1          # peer cell starved / source unmeasured - refuse to guess


# Phrases the renderer must never emit, in any language we write (M4).
FORBIDDEN_PHRASES = ("omission confirmed", "confirmed omission", "누락 확정", "확정 누락")

_HEADLINES = {
    Form.PRESENT: "present in its standard place",
    Form.CANDIDATE_OMISSION: "candidate omission - 10-K confirmation REQUIRED",
    Form.REPORTED_ELSEWHERE: "reported elsewhere (umbrella/parallel tag)",
    Form.DERIVABLE_SUBTOTAL: "derivable subtotal (components disclosed)",
    Form.NOT_APPLICABLE: "not applicable to this business",
    Form.INDUSTRY_HOMONYM: "industry homonym - concept word means something else here",
    Form.NO_VERDICT: "no verdict - refusing to judge on a starved or unmeasured basis",
}


@dataclass(frozen=True)
class Verdict:
    form: Form
    evidence: str  # one line quoting observed values - mandatory

    def __post_init__(self):
        if not self.evidence or not self.evidence.strip():
            raise ValueError("a verdict without an evidence line is a blacklist entry")

    def render(self) -> str:
        text = f"[{self.form.name}] {_HEADLINES[self.form]} | evidence: {self.evidence}"
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in text.lower():
                raise AssertionError(
                    f"renderer produced a forbidden certainty phrase {phrase!r} - "
                    f"this output path must not exist"
                )
        return text


def adjudicate(
    concept: Concept,
    face_tags: frozenset[str] | set[str],
    notes_tags: frozenset[str] | set[str],
    sic: str,
    concept_evidence: bool | None,
) -> Verdict:
    """Classify one (company, concept) observation into a form.

    Args:
        face_tags / notes_tags: tag names present in each dataset for this
            filing (contract 2: absence only counts when BOTH are silent).
        sic: 4-digit SIC of the filer.
        concept_evidence: does independent evidence say the concept exists in
            this business (e.g. lease expense, ROU asset)? None = unknown.
    """
    seen = frozenset(face_tags) | frozenset(notes_tags)

    present_main = [t for t in concept.main_tags if t in seen]
    if present_main:
        return Verdict(Form.PRESENT, f"standard tag {present_main[0]} observed")

    if any(sic.startswith(p) for p in concept.homonym_sic_prefixes):
        return Verdict(
            Form.INDUSTRY_HOMONYM,
            f"SIC {sic} is on the {concept.key} homonym exclusion list (growing, not complete)",
        )

    present_umbrella = [t for t in concept.umbrella_tags if t in seen]
    if present_umbrella:
        return Verdict(Form.REPORTED_ELSEWHERE, f"umbrella tag {present_umbrella[0]} observed")

    if concept.part_tags and all(t in seen for t in concept.part_tags):
        return Verdict(
            Form.DERIVABLE_SUBTOTAL,
            f"all components observed ({', '.join(concept.part_tags)}) - subtotal is computable",
        )

    if concept_evidence is False:
        return Verdict(
            Form.NOT_APPLICABLE,
            f"no independent evidence of {concept.key} in this business",
        )
    if concept_evidence is None:
        return Verdict(
            Form.NO_VERDICT,
            f"{concept.key} evidence unknown - refusing to call absence without it",
        )
    return Verdict(
        Form.CANDIDATE_OMISSION,
        f"no {concept.key} tag in face or notes dataset despite concept evidence",
    )
