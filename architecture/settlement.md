# Settlement

**Status:** Implemented

Settlement is the durable-history vertical: the place protocol facts are committed so that anyone can verify them later. It is a hash-chained, append-only, publicly verifiable transparency log on Postgres, with no validator set and no consensus, because nothing written to it is contested.

Three rules frame everything below. Settlement is not the general-purpose query database. One protocol event is never one settlement transaction. Settlement is a transparency log, not a blockchain ([ADR 0186](decisions/0186-no-blockchain-validator-consensus-transparency-log-only.md), [ADR 0070](decisions/0070-settlement-is-a-public-transparency-log.md)).

Deeper topics have their own pages: [mirroring and equivocation detection](settlement/mirroring.md), [sharding and cross-shard commitment](settlement/sharding.md), and [retention and ledger growth](settlement/retention-and-growth.md).

## Durable history, not a database

Settlement is responsible for durable commitments, provenance, canonical protocol history, verifiable attestations, durable identity facts, guild history, integrator and issuer registration, and key lifecycle. It is not responsible for fast reads; that is [query and indexing](query-and-indexing.md). A mutable Postgres row is never the ultimate authority for something Avalon promises to preserve.

## Batching

```text
Event 1
Event 2
...
Event N
    |
Batch                    (EventBatch)
    |
Merkle tree / commitment (Commitment)
    |
Settlement               (SettlementProvider::commit)
```

One transaction per event does not scale and is never the design. Events accumulate in a buffer (the outbox), are batched, a commitment is computed over the batch, and the commitment is what gets settled. Each entry records the batch it was committed with, each batch has one row, and verification recomputes a batch's root from its entries rather than trusting a stored value.

The outbox is what makes a domain write and its ledger-bound event atomic: the handler writes both in one Postgres transaction, and a background worker later folds pending outbox rows into the log. A crash between the two cannot orphan either. There is a window, on the order of the worker's poll interval, in which an event is durable but not yet visible in the log.

How large a batch is and how often commitments are produced are tuning questions ([scalability](scalability.md)). Today a batch closes whenever the worker's drain tick runs, not on a size threshold or a timer, and a single-event batch is legal. Only one worker drains at a time per database (a Postgres advisory lock), so two processes cannot commit the same pending rows twice.

## The boundary

The settlement boundary is one trait:

```rust
#[async_trait]
pub trait SettlementProvider: Send + Sync {
    async fn commit(&self, batch: &EventBatch) -> Result<Commitment, SettlementError>;
    async fn verify(&self, commitment: &Commitment) -> Result<bool, SettlementError>;
    async fn get_commitment(&self, batch_id: Uuid) -> Result<Commitment, SettlementError>;
}
```

This trait is the only thing outside the settlement component that may depend on it. The protocol types, the server, the SDKs, and every integrator integration are indifferent to how a commitment is produced. Consensus, block production, and peer-to-peer networking do not belong on this trait.

## Design decisions

- **Attestations before blockchain.** Durable facts need to behave like a verifiable ledger, meaning tamper-evident and independently verifiable. A signed, append-only store provides that without a chain ([ADR 0068](decisions/0068-attestations-before-blockchain-chain-architecture-left-open.md)).
- **A public transparency log.** Every durable fact is a signed, hash-chained, append-only entry. Anyone can verify an entry and its position without permission, and anyone can mirror the log and serve reads. Federation is rejected, because visibility must not depend on which server an integrator trusts.
- **Postgres, permanently.** Real transparency logs (Certificate Transparency, Sigsum, Trillian) run on ordinary SQL backends, because verification happens by fetching Merkle proofs over the network, not by every party holding a full replica the way a blockchain full node does. An earlier decision to use an embedded RocksDB store ([ADR 0177](decisions/0177-embedded-ledger-storage-engine-is-rocksdb.md)) was superseded.
- **No blockchain, no validator or BFT consensus.** Consensus exists to adjudicate contention over a single, shared, scarce resource (the double-spend problem). Nothing settlement records is contested: `identity.created`, `achievement.issued`, `friend.requested`, `guild.created`, and `game.registered` are each a fact asserted by exactly one party about something only that party has authority over; for the friend and guild kinds that party is today the recording node acting for an authenticated session, not the actor's key (see [signing posture](../protocol/protocol-events.md#signing-posture)). There is no native currency or token. An earlier decision to run Avalon's own BFT chain ([ADR 0093](decisions/0093-avalon-operates-its-own-chain-no-native-currency-at.md)) was superseded in part by [ADR 0186](decisions/0186-no-blockchain-validator-consensus-transparency-log-only.md). A cross-integrator currency layer is a later, optional, separately decided phase ([future layers](future-layers.md)); only if it is ever proposed does consensus become a question again, scoped to that feature.

## Log structure

The hash and Merkle structure and the signing scheme follow RFC 6962 (Certificate Transparency) rather than a bespoke design.

- **Two structures.** A sequential hash chain gives cheap per-link tamper evidence. Each `entry_hash` is the SHA-256 of one fixed binary layout (domain tag `avalon.ledger.entry`) covering the network id, the shard id, the sequence number, the previous entry hash, the event id, kind, issuer, subject, the event time in microseconds, and the SHA-256 of the entry's [canonical payload](../protocol/protocol-events.md#canonical-payloads-and-signing-bytes). The entry commits to the payload hash rather than the payload bytes, so a row whose payload has been pruned still recomputes to the same hash. On top of it, a single append-only Merkle tree over all `entry_hash` values ordered by sequence number, computed with RFC 6962's tree-hashing algorithm, gives succinct inclusion and consistency proofs that a plain chain cannot.
- **The batch root is the whole ledger's tree root** as of that batch, not a per-batch subtree. `tree_size` is always the real leaf count, never the last sequence number: Postgres identity values are not transactional, so a rolled-back batch burns sequence numbers and the two can diverge.
- **Signed Tree Heads, not per-entry signatures.** One `SignedTreeHead { tree_size, root_hash, network_id, timestamp, signing_key_id, signature }` is produced per batch commit, in the same transaction, signed with Ed25519 by the settlement operator's key. That key is a separate key domain from issuer keys and identity keys. An inclusion proof anchored to one valid signed head lets anyone verify an entry belongs to the endorsed tree.
- **Mirror sync is minimal.** The log exposes the latest head, a historical head by tree size, RFC 6962 consistency proofs (the tree at size A is an append-only prefix of the tree at size B), and inclusion proofs. Two different heads for the same tree size are cryptographic proof of operator equivocation. See [mirroring](settlement/mirroring.md).
- **Trust in a head need not rest on one key.** Independent witnesses can cosign a head after checking it only grew, and a verifier accepts it once a majority of its known witness list has cosigned. See [witness cosigning](../protocol/witness-cosigning.md) and [network trust anchors](../protocol/network-trust-anchors.md).
- **Genesis and network identity.** A ledger is committed once, at first boot, to a `network_id`; every later boot verifies the configured value against the stored one and refuses to start on a mismatch. `network_id` and the shard id are hashed into every entry, so two ledgers with different identities have disjoint hash spaces and a private instance's entries cannot be spliced into the public chain. See [self-hosting](self-hosting.md).

## Verification

`verify` runs two independent checks, and both must pass.

1. A hash-chain check replays a batch's entries across the sequential chain (the previous hash must match, and every entry hash is recomputed from the stored fields and payload hash; where the payload is present it is re-hashed and compared with the stored payload hash). It catches content tampering that left the stored hash stale.
2. A Merkle check recomputes the RFC 6962 tree hash freshly from every `entry_hash` up to the batch's last entry and compares it with the commitment. It catches structural tampering (an altered hash, reordering, a deleted row) anywhere up to that batch. It uses only `entry_hash`, never payloads, so [payload pruning](settlement/retention-and-growth.md) never affects it.

The ledger-inspection command re-hashes every row, checks every link, and then verifies the signed tree head against the operator's verify key.

## Public read API

The read side is public and unauthenticated, because a transparency log must be verifiable by anyone holding only the operator's verify key.

| Read | Purpose |
| --- | --- |
| `GET /ledger/sth/latest` | The current signed tree head. |
| `GET /ledger/sth/{tree_size}` | The head at exactly that size (404 if no batch closed at that size). |
| `GET /ledger/proof/consistency?first=&second=` | An RFC 6962 proof that the tree at `second` extends the tree at `first`. |
| `GET /ledger/proof/inclusion?seq=&tree_size=` | An inclusion proof for the entry with that sequence number, including its leaf index. Sequence numbers can have gaps, so the leaf index is the entry's rank, not `seq - 1`. |
| `GET /ledger/entries?since_seq=&limit=` | Bulk entry content in sequence order, capped per request. Not itself a verified read; callers verify each entry with an inclusion proof. `subject=` narrows it to one subject's entries. |
| `GET /ledger/cross-shard-root` | The cross-shard root; see [sharding](settlement/sharding.md). |

Every proof is independently re-verified before the response is built, so a wrong proof never leaves the process. A sequence number or tree size beyond what has been committed is a 404, never an empty proof. One write route exists, `POST /ledger/submit`, which is node-to-node and authenticated with a shared secret; a node without that secret configured refuses every request to it. The wire descriptions of the API are in [protocol API](../protocol/api.md).

## Query reads are not settlement reads

Two narrow exceptions exist where the server reads the log directly rather than through the indexer: a caller's own history (`GET /me/history`, scoped by construction to the authenticated identity) and the subject-filtered entries read above. Neither is a general query surface, so neither crosses the "not the general-purpose query database" boundary. See [query and indexing](query-and-indexing.md).

## Implementation

Status: Implemented. The Postgres provider, the RFC 6962 Merkle code (with an incremental O(log n) tree cached in memory and rebuilt on restart), tree-head signing, and the outbox worker are in the [settlement crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/chain) and the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol. Head signing and verification live in the [protocol crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/protocol) so clients can verify without a database dependency. The merkle implementation is tested against the reference vectors published by `transparency-dev/merkle`.

Undecided or unbuilt: a formal export format for the log (the log is exportable in principle through the public read API); a persisted Merkle node table to avoid the in-memory rebuild at startup (a possible optimization if startup time becomes a problem).

## Related

- [Mirroring and equivocation detection](settlement/mirroring.md)
- [Sharding and cross-shard commitment](settlement/sharding.md)
- [Retention and ledger growth](settlement/retention-and-growth.md)
- [Query and indexing](query-and-indexing.md)
- [Nodes](nodes/README.md)
- [Protocol events](../protocol/protocol-events.md), [worked ledger example](../protocol/worked-ledger-example.md)
- [Network trust anchors](../protocol/network-trust-anchors.md), [witness cosigning](../protocol/witness-cosigning.md)
- [ADR 0070](decisions/0070-settlement-is-a-public-transparency-log.md), [ADR 0186](decisions/0186-no-blockchain-validator-consensus-transparency-log-only.md)
