# ADR-0070: Settlement Is a Public Transparency Log — Not Federation, Not Blockchain Consensus

**Status:** Accepted — decided 2026-09-07

Original record: [avalon-protocol#70](https://github.com/avalon-initiative/avalon-protocol/issues/70). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

The open question in #40 ("what does `avalon-chain`'s `SettlementProvider` eventually become") was framed as a choice between a custom appchain, adopting an existing blockchain, or staying Postgres-backed indefinitely. Working through what property Avalon actually needs surfaced that neither "blockchain" option in that framing is the right shape, and neither is federation:

- **Federation** (independent server instances, each deciding whether to trust/whitelist another) fails the actual requirement. It makes whether a game can see a player's identity conditional on which server that game happens to peer with — which quietly recreates the platform-locked walled gardens `docs/WhyAvalon.md` argues against. A player's identity must be an all-or-nothing fact any Avalon-integrated game can read, not something that varies by which server it trusts.
- **Mining-based consensus** (Bitcoin-style proof-of-work/stake) solves a problem Avalon doesn't have. It exists to let mutually distrusting parties agree on who writes next when they're contesting a scarce resource (a coin that can't be spent twice). Avalon's writes are already unambiguous — a game signs its own achievement issuance, a player signs their own identity/profile claim. There is no write-ordering conflict between distrusting parties to referee, so consensus machinery buys nothing here at enormous engineering cost.

## Decision

Avalon's durable settlement layer is a **public transparency log** — the same pattern Certificate Transparency uses for TLS certificates — not federation and not a mining/consensus blockchain:

- Every durable protocol fact (identity created, achievement issued, etc.) is a signed, hash-chained, append-only entry.
- Any party can independently verify an entry's signature and its position in the log without asking anyone's permission.
- Any party can mirror the full log and serve reads from their own copy. A client doesn't pick "which server to trust" the way federation requires — a mirror can't misrepresent the log's contents without that being independently detectable, because the log is self-verifying.
- This requires no mining, no proof-of-work, no validator voting, and no bilateral peering agreements between operators.

Milestone 1 stays exactly what #68 already decided: a signed, append-only Postgres-backed store (`avalon-chain`'s current `PostgresSettlementProvider` stub). What this ADR adds is a constraint on that implementation going forward: the schema and signing scheme must be designed so entries are independently verifiable and the log is exportable/mirrorable from day one, not bolted on retroactively once multiple operators exist.

## Consequences

- #40 is narrowed, not closed: "custom appchain vs. existing chain vs. staying Postgres" is replaced by the actual remaining open question — the concrete technical design of the transparency log (hash-chaining/Merkle structure, signed-tree-head cadence, mirror sync protocol, what the milestone-1 Postgres schema needs to support this from the start).
- `docs/Proposal.md` §14 (Blockchain), §20 (Self-Hosting and Decentralization), and Guiding Principle 7 are updated to state this directly rather than leaving "blockchain, maybe, eventually" open-ended.
- Federation (independent, mutually-peering server instances with siloed user bases) is rejected as a model for identity/settlement. Self-hosting is still a goal — multiple organizations running infrastructure — but as mirrors of one shared, publicly verifiable log, not as siloed instances requiring bilateral trust.
