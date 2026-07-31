"""why-missing adjudicator - answers "why is this amount not in standard XBRL".

TRL 4 scaffold: pure judgement modules, contracts pinned by tests/.
I/O against SEC lives behind identity/freshness gates; no module here
performs network access at import time.
"""
from adjudicator.concepts import FlowConceptRejected, resolve
from adjudicator.verdict import Form, Verdict, adjudicate

__all__ = ["resolve", "FlowConceptRejected", "adjudicate", "Form", "Verdict"]
