# ADR-0186: No Blockchain / Validator Consensus — Transparency Log Only, Unless Cross-Game Currency Is Later Proposed

**Status:** Accepted — decided 2026-09-09

Original record: [avalon-protocol#186](https://github.com/avalon-initiative/avalon-protocol/issues/186). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

#184 questioned whether ADR #93's "permissioned validator set reaching
Byzantine-fault-tolerant agreement on block order" conclusion actually
follows from its own stated premise — that Avalon's writes are already
unambiguous (each actor signs its own claim) and there's no scarce resource
to referee. Consensus of any kind exists to solve contention over a single,
shared, mutable, scarce resource (the double-spend problem). Settlement
records `identity.created`, `achievement.issued`, `friend.requested`,
`guild.created`, `game.registered` — every one a fact asserted by exactly
one authoritative signer about something only that signer has authority
over. None of it is contested. There is no double-spend anywhere in this
list, because there is nothing scarce being written to.

## Decision

**Avalon does not build a blockchain, and does not adopt validator/BFT
consensus, for settlement.** The durable ledger is (and stays) a
transparency log — hash-chained, tamper-evident, publicly verifiable — with
no global consensus round required to accept a write, because no write
competes with another for the same resource. `PostgresSettlementProvider`
(or an equivalent conventional database-backed store) is a legitimate
permanent backend for this, not a milestone-1 stand-in for something more
"real" — the Certificate-Transparency/Sigsum/Trillian precedent runs
production-grade transparency logs on ordinary SQL backends, because
verification happens via Merkle proofs fetched over the network, not by
every party independently holding a full replicated copy the way a
blockchain full node does.

**This is scoped specifically to settlement of protocol facts — identity,
attestations, social graph, guild history, provenance.** It does not
pre-decide anything about a hypothetical future cross-game currency or
payments feature. If Avalon ever introduces a native crypto-asset or
cross-game currency (Proposal.md §15/§27, always described there as later
and optional), *that* feature genuinely would introduce a scarce, contested
resource — and at that point, and only at that point, consensus becomes a
real question worth reopening, scoped to that feature specifically. This ADR
is not a blanket ban on ever discussing consensus again; it closes the
question for settlement-as-currently-scoped and requires a fresh decision if
currency is ever actually proposed.

## Consequences

- #40's scope shrinks: the validator-admission/BFT-algorithm design work it
  inherited from ADR #93 is dropped. What may remain (witnessed checkpoints
  to detect operator equivocation, if Avalon ever runs multiple independent
  operators) is a materially smaller, separate design question — not filed
  as its own ticket here; revisit if/when Avalon actually has more than one
  settlement operator to coordinate.
- #178 (RocksDB-backed `SettlementProvider`) is closed, won't-fix — its
  per-node-embedded-store rationale ("each validator/mirror holds its own
  local copy, synced peer-to-peer") was blockchain full-node thinking that
  no longer applies. The implementation was reverted (#179 reverted via
  #185) rather than left merged-but-dormant.
- ADR #177 (RocksDB as the storage engine choice) is superseded — the
  question it answered no longer needs answering, since there's no
  validator/full-node model requiring an embedded per-node engine at all.
- `docs/architecture/settlement.md` needs a follow-up update reflecting this
  (tracked as part of landing this ADR, not a separate ticket).
- ADR #93's "permissioned validator set" conclusion is superseded by this
  ADR; its no-currency-at-launch and no-external-anchoring conclusions are
  untouched.

## Related

Resolves #184. Supersedes part of #93 (closed) and ADR #177 (closed).
Narrows #40. Closes #178 (won't-fix). Reverts #179 (via #185, merged).
