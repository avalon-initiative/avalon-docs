# Architectural decisions

**Status:** Reference

Decisions that shape Avalon as a whole are recorded here. Each is a numbered record of what was decided, why, and what else was considered.

## Numbering and history

Decisions were recorded as closed GitHub issues labeled [`architecture-decision-record`](https://github.com/avalon-initiative/avalon-protocol/issues?q=is%3Aissue+label%3Aarchitecture-decision-record) in `avalon-protocol`. The ADR number is that issue number, so existing references to `#76` and similar keep working. Each file preserves the recorded text unchanged and links its original issue.

A decision is never rewritten to make the current design look cleaner. When a later decision replaces an earlier one, the earlier record keeps its text and gains a note pointing to its successor.

## Avalon-wide decisions

| ADR | Decision | Area | Status | Decided |
|---|---|---|---|---|
| [0067](0067-identity-is-separate-from-game-characters.md) | Identity Is Separate From Game Characters | Identity | Accepted | 2026-09-07 |
| [0068](0068-attestations-before-blockchain-chain-architecture-left-open.md) | Attestations Before Blockchain (Chain Architecture Left Open) | Settlement | Accepted | 2026-09-07 |
| [0070](0070-settlement-is-a-public-transparency-log.md) | Settlement Is a Public Transparency Log — Not Federation, Not Blockchain Consensus | Settlement | Accepted | 2026-09-07 |
| [0074](0074-guilds-are-network-level-primitives-not-game-owned.md) | Guilds Are Network-Level Primitives, Not Game-Owned | Guilds | Accepted | 2026-09-08 |
| [0075](0075-durable-protocol-history-is-canonical-query-databases-are-projections.md) | Durable Protocol History Is Canonical; Query Databases Are Projections | History and query | Accepted | 2026-09-08 |
| [0076](0076-attestation-trust-model-authenticity-validity-and-recognition-are-separate.md) | Attestation Trust Model — Authenticity, Validity, and Recognition Are Separate | Trust | Accepted | 2026-09-08 |
| [0077](0077-the-hub-is-a-client-of-the-network-not.md) | The Hub Is a Client of the Network, Not the Network | Ecosystem boundaries | Accepted | 2026-09-08 |
| [0078](0078-realtime-presence-is-ephemeral-and-never-enters-durable-history.md) | Realtime Presence Is Ephemeral and Never Enters Durable History | Realtime | Accepted | 2026-09-08 |
| [0093](0093-avalon-operates-its-own-chain-no-native-currency-at.md) | Avalon Operates Its Own Chain — No Native Currency at Launch | Settlement | Accepted, superseded in part | 2026-09-08 |
| [0177](0177-embedded-ledger-storage-engine-is-rocksdb.md) | Embedded Ledger Storage Engine Is RocksDB | Settlement | Superseded | 2026-09-09 |
| [0186](0186-no-blockchain-validator-consensus-transparency-log-only.md) | No Blockchain / Validator Consensus — Transparency Log Only, Unless Cross-Game Currency Is Later Proposed | Settlement | Accepted | 2026-09-09 |
| [0437](0437-three-tier-data-freshness-policy-realtime-push-poll-or.md) | three-tier data-freshness policy — realtime push, poll, or stale-until-refetch | Data freshness | Accepted | 2026-09-15 |
| [0479](0479-network-isolation-via-per-network-issuer-registration-not-signature.md) | Network Isolation Via Per-Network Issuer Registration, Not Signature Binding | Networks and trust | Accepted | 2026-09-19 |
| [0672](0672-realtime-websocket-extraction-proxies-through-gateway-not-direct-connect.md) | Realtime WebSocket extraction proxies through Gateway, not direct-connect | Nodes | Accepted | 2026-09-20 |
| [0786](0786-on-demand-cross-node-identity-data-resolution.md) | On-Demand Cross-Node Identity Data Resolution | Nodes and identity | Accepted | 2026-09-23 |
| [0903](0903-node-participation-must-not-depend-on-public-reachability-nat.md) | node participation must not depend on public reachability (NAT-aware connectivity) | Nodes and networking | Accepted | 2026-09-25 |
| [1009](1009-how-far-does-ledger-pruning-go-past-payload-nulling.md) | how far does ledger pruning go past payload-nulling — checkpoint/archive tiering for skeleton rows? | History and retention | Accepted | 2026-09-28 |

## Decisions that stay with an implementation

These concern how `avalon-protocol` is built rather than how Avalon works, so they remain as issues in that repository:

- [avalon-protocol#69](https://github.com/avalon-initiative/avalon-protocol/issues/69): the Rust workspace is six crates, with no further consolidation.
- [avalon-protocol#593](https://github.com/avalon-initiative/avalon-protocol/issues/593): the reference server enables the DHT by default (opt-out).

## Open decisions

A question still being decided is an open issue labeled [`decision`](https://github.com/avalon-initiative/avalon-protocol/issues?q=is%3Aissue+is%3Aopen+label%3Adecision); it becomes an ADR when it closes.

## Format

Records use Context, Decision, Consequences, and Related sections. Some older ones add Why and Alternatives considered.

## Related

- [Architecture overview](../overview.md)
- [Documentation guide](../../developers/documentation-guide.md)
