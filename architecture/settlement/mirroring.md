# Mirroring and Equivocation Detection

**Status:** Implemented

A mirror is a node that independently copies and verifies another node's settlement log and re-serves it. Mirroring is how Avalon achieves multiple operators without federation: it is the Certificate Transparency pattern, where any mirror that misrepresents the log is detectable because the log is self-verifying.

This page covers how a mirror verifies what it copies, how it detects a log operator that shows different histories to different parties, and how it is woken early. The log itself is described in [settlement](../settlement.md).

## Mirrors, not federation

Under federation, whether integrator B can see an identity would depend on which servers B's server peers with, recreating the walled gardens Avalon exists to remove. Under mirroring, a client does not pick which server to trust: a mirror that misrepresents the log is detectable. The log is Avalon's own, not an anchor into someone else's chain, and that does not change this ([ADR 0070](../decisions/0070-settlement-is-a-public-transparency-log.md)).

Mirroring addresses read decentralization: anyone can verify the log without trusting whichever node they asked. Sharded authority ([sharding](sharding.md)) addresses the complementary write and control problem. Running a mirror is one of three meanings of "self-host"; see [self-hosting](../self-hosting.md).

## How a mirror verifies

A mirror watches one or more configured peers. Every tick, for each peer, it:

1. Fetches the peer's latest signed tree head and verifies its signature, using the verify key resolved from the trust anchor for the peer's claimed `network_id`. A peer claiming an unpinned `network_id` is refused outright ([network trust anchors](../../protocol/network-trust-anchors.md)).
2. Records the head as an observation, separate from the heads this node itself produced as an authority.
3. Compares it with every other observation at the same network and tree size (from other peers, and from this node's own signed history if it has one).
4. Chooses the tree head that this tick's peers most widely agree on. This is a majority-corroboration gate, not "whichever peer answered first".
5. Backfills entries after the last verified sequence number, and for each one fetches an inclusion proof and checks it against the corroborated head before storing it. Requests round-robin across the corroborating peers; if none can supply a verifiable entry the whole pass aborts and retries next tick rather than accepting a partial backfill.

Mirrored history is stored separately from authored history (a node can be authority for one shard and mirror of another). Mirror state is keyed by both `network_id` and shard, since every shard has its own sequence and tree-size numbering. Once an entry's inclusion is verified it is also decoded and applied to the node's local indexer in the same transaction, so a node with no settlement role of its own can serve independently verified reads from its own database.

A restart is not a special case: backfill resumes from the last verified sequence number.

## Equivocation detection

If two different root hashes are observed for the same network, shard, and tree size, the log operator signed two different histories. Both heads are validly signed, so there is no automatic correct answer.

- The mismatch is durably recorded as a finding and logged as a structured error event, so an operator or alerting system can act on it.
- A mirror refuses to backfill past a tree size with an unresolved finding.
- Resolving a finding (recording which root was legitimate) and discarding mirrored entries that followed the losing branch are explicit, human-driven recovery steps. There is deliberately no automatic "pick the right head" logic.

This is detection, not prevention. Witness cosigning ([witness cosigning](../../protocol/witness-cosigning.md)) strengthens it: a verifier accepts a head only once a majority of its known witnesses have cosigned it, and two conflicting heads that both reach a majority must share a witness, making a forked log provable from signatures.

## Push-assisted sync

Polling is the baseline and always works. On top of it, a mirror can register interest in a network through the same DHT-backed interest mechanism realtime uses ([distributed topology](../distributed-topology.md)). When an authority commits a batch, it looks up registered mirrors and posts a small notification to each over plain HTTP. The notification carries nothing the mirror trusts: it only wakes the watcher's loop early, which then runs the same verify, corroborate, and backfill pipeline. A missed or dropped push is never fatal; the next poll tick catches up. Registration is per network the mirror has successfully verified a head for, never an unverified one.

## Replication signals

Mirrors expose how far they have independently verified another node's history. Two mechanisms use this: hot-tier nodes only prune payloads that enough mirrors confirm, and a shard below a minimum number of confirmed mirrors stops accepting new identity registrations once past a bootstrap grace period ([retention and growth](retention-and-growth.md)).

## Implementation

Status: Implemented. The mirror watcher, equivocation detection, and the push notification handler are in the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) and the [settlement crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/chain) of avalon-protocol. The operator runbook for a real equivocation and the manual promotion of a mirror to authority are in the [avalon-protocol docs](https://github.com/avalon-initiative/avalon-protocol/tree/main/docs). Authority promotion is deliberately manual, never automatic election, because automatic election would reopen the no-consensus decision.

## Related

- [Settlement](../settlement.md)
- [Sharding and cross-shard commitment](sharding.md)
- [Nodes](../nodes/README.md)
- [Self-hosting](../self-hosting.md)
- [Witness cosigning](../../protocol/witness-cosigning.md), [network trust anchors](../../protocol/network-trust-anchors.md)
