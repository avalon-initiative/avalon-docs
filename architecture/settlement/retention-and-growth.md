# Retention and Ledger Growth

**Status:** Implemented — with the open questions listed at the end

Not every settlement node needs to store every raw event body forever, and not every kind of data belongs in the ledger at all. This page covers the retention tiers that let a node discard old event bodies without weakening verification, the checkpoint that lets a node bootstrap without full replay, and the rules that bound how fast the log grows.

The log itself is described in [settlement](../settlement.md).

## Retention tiers

The commitment (the hash-chained, Merkle-committed log) stays small and permanent on every settlement node regardless of tier. Tiering applies only to the raw signed event bodies (payloads) behind each commitment.

| Tier | Retains | Typical operator |
| --- | --- | --- |
| Full (archive) | complete history | a dedicated archive operator willing to carry long-term storage |
| Hot | a configurable recent window of history (a number of days of commit time) | a normal node optimized for current read and serve traffic |

Tier is independent of a node's capability roles and of its shard role. An authority can be hot or full for the shard it authors; a mirror can independently be hot or full. Pruning only ever affects the node's own authored payloads; mirrored history is not touched.

A hot node may discard payloads older than its window only when the network still retains them elsewhere: never discard something nothing else retains. This is enforced in code when configured: before each pruning pass the node asks configured archive peers how far they have independently verified and mirrored its history, and it prunes only past a boundary that at least a minimum number of distinct peers confirm. Declaring a hot tier alone changes nothing; pruning is a second, off-by-default opt-in, and the confirmation gate is a third.

**What pruning touches.** Pruning nulls out the payload column only. Sequence number, entry hash, previous hash, kind, issuer, subject, timestamp, version, and batch id are never touched, which keeps a pruned row's place in the hash chain and the Merkle tree (built only from `entry_hash`) intact. Verification treats a missing payload as "not independently re-checkable from here", never as tampering, and a batch with one pruned and one tampered entry still fails. Inspection tools report whether a node holds full or partially pruned history, derived from the data.

How far pruning could go beyond payload nulling (for example dropping whole rows) is an open decision: [ADR 1009](../decisions/1009-how-far-does-ledger-pruning-go-past-payload-nulling.md).

## Minimum replication for new registrations

A related gate protects durability rather than storage. A shard that does not yet have enough independently confirmed mirrors is a shard whose data could be lost with one machine, so once it is past a bootstrap grace period it stops accepting new identity registrations until enough distinct, currently fresh mirrors confirm it. Identities already registered are never disrupted. A young single-operator shard is exempt during the grace period, and a node that cannot yet tell the shard's age treats it as young. The node reports its confirmed mirror count and eligibility in its status so an operator sees the problem before a registration fails. One minimum applies to every shard; per-shard-type configuration does not exist yet.

## Settlement-state checkpoint

For the commitment layer, the latest signed tree head is the checkpoint: a signed `(tree_size, root_hash)` at a known height, produced every batch with no extra storage. A bootstrapping or hot node trusts that head as the root for everything at or before its size, then only needs entries newer than its window.

Not covered: a snapshot of indexer projections. Rebuilding the read model is still a full replay from genesis ([disaster recovery](../disaster-recovery.md)). A projection snapshot format is an open follow-up.

## Bounding ledger growth

Standing rule: high-frequency ephemeral data never touches the ledger. Guild chat and direct-message content do not enter the ledger, and each is enforced by a dedicated source-scanning test rather than by convention. A new feature that wants a durable write asks first whether it is paced by human-scale actions (identity, friendship, guild membership, achievements) or is machine-speed, high-cardinality data that belongs in rebuildable projections. In the latter case a similar enforcement test is added.

Two controls exist for legitimate growth:

- **Per-issuer-subject write quota.** A volume-only floor on attestation writes for one `(issuer, subject)` pair over a rolling window. A write, or a whole bulk call, that would cross it is rejected with `429`, never partially applied. It never inspects what is attested, only volume.
- **Subject-scoped selective sync.** The bulk entries read can be filtered to one subject, so one subject's history is cheap to fetch without replaying the log. The filter matches the exact subject string (which includes the event verb), and filtering never changes an entry's position, so inclusion proofs still verify against the same global tree.

Two costs remain open: how many events one issuer can write about one subject, and a structural bound on long-run per-subject growth (log compaction or checkpointing), which has been considered and deferred as not needed at current scale.

## Implementation

Status: Implemented. Tier configuration, the pruning worker, the archive-confirmation gate, and the replication gate are in the [settlement crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/chain) and [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol; the ledger CLI has a manual prune command with a dry-run mode. Configuration variables are documented with the [hosting docs](https://github.com/avalon-initiative/avalon-protocol/tree/main/docs).

## Related

- [Settlement](../settlement.md)
- [Mirroring and equivocation detection](mirroring.md)
- [Disaster recovery](../disaster-recovery.md)
- [Scalability](../scalability.md)
- [ADR 1009](../decisions/1009-how-far-does-ledger-pruning-go-past-payload-nulling.md)
