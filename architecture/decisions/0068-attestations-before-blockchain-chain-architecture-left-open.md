# ADR-0068: Attestations Before Blockchain (Chain Architecture Left Open)

**Status:** Accepted — decided 2026-09-07

Original record: [avalon-protocol#68](https://github.com/avalon-initiative/avalon-protocol/issues/68). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

> Its open chain-architecture question was settled by later records: see [ADR-0070](0070-settlement-is-a-public-transparency-log.md) and [ADR-0186](0186-no-blockchain-validator-consensus-transparency-log-only.md).

# ADR 0002: Attestations Before Blockchain, Chain Architecture Deferred

**Status:** Decided. The chain-architecture question this ADR left open is now
settled — see [#79](https://github.com/avalon-initiative/avalon-protocol/issues/79)
and [ADR #93](https://github.com/avalon-initiative/avalon-protocol/issues/93):
Avalon operates its own chain, no native currency at launch.

## Context

Avalon needs a durable, verifiable record of protocol facts — achievements issued,
guild membership changes, asset ownership transfers — that a receiving game can
independently verify without trusting a central database blindly. The first
instinct is "put it on a blockchain." `docs/stakeholders/Proposal.md` (§14,
Guiding Principle 7) argues against that for milestone 1:
real-time gameplay data must never touch a chain, and even durable protocol facts
don't need one from day one — they need to *behave like* a verifiable ledger
(tamper-evident, independently verifiable), which a signed, append-only Postgres
table already provides.

Mid-design, a chain-first framing was raised directly ("avalon-protocol is going to
be the blockchain we use to carry player ID and enable auth"), including whether to
build a fully custom appchain (own consensus, block/DAG production, P2P networking
— Kaspa-style BlockDAG was raised as a research reference, not a decision, and
still is: see `docs/architecture/settlement.md`) from day one. That direction was reversed back to the deferred approach
below, specifically *because* it needs to stay swappable later — hence this ADR
exists to record the swap point as a first-class open decision, not something
settled by default.

## Decision (settled)

Milestone 1 uses a signed, append-only ledger — not a blockchain:

```text
Game
  │ high-volume events
  ▼
Event Buffer (filter/aggregate)
  ▼
Durable Protocol Events
  ▼
Batch → Commitment
  ▼
SettlementProvider (Postgres-backed impl for now)
```

The `chain` crate defines a `SettlementProvider` trait (`commit(batch)`,
`verify(commitment)`, `get_commitment()`) and ships exactly one implementation: a
Postgres-backed store of signed batches. No consensus, no P2P networking, no block
production in milestone 1.

## Decision (resolved by #79 / ADR #93)

What `SettlementProvider` implementation Avalon eventually moves to was left
open here on purpose, precisely so the trait boundary below would hold
regardless of the answer. It has since been decided: **Avalon operates its own
chain**, not an anchor to an existing one and not a deep integration with an
existing chain's token — see [ADR #93](https://github.com/avalon-initiative/avalon-protocol/issues/93).
No native currency at launch. The concrete consensus and validator design is
still open engineering work, tracked in
[#40](https://github.com/avalon-initiative/avalon-protocol/issues/40), and still
needs the research spike this ADR always called for — a custom chain is not to
be chosen, or built, "merely because it is fashionable," and the evaluation
criteria in `docs/architecture/settlement.md` still apply to that design.

The trait boundary this ADR established did its job: nothing in `protocol`,
`server`, `sdk`, or any game integration had to change when the backend
question resolved.

## Consequences

- `chain`'s public surface is the `SettlementProvider` trait plus the Postgres
  implementation. Nothing else in the workspace depends on Postgres directly for
  settlement.
- Milestone 1 is unaffected: the hash-chained Postgres ledger stays the
  implementation until the chain itself exists.
