"""Single source of pinned constants (crm AD-4 discipline ported).

Every value carries a `# source:` label - measured, policy, or convention.
Nothing here is derived from data at import time.
"""

# source: party verdict 2026-07-29, measured on 5,388 filers - n>=5 violates the
# four-peers-is-gossip condition, n>=20 eats 10% of the quarry.
PEER_MIN_CELL = 10

# source: SEC fair-access policy (convention).
SEC_USER_AGENT = "daria.j.kim@gmail.com why-missing adjudicator"
SEC_RATE_SLEEP_SECONDS = 0.11
