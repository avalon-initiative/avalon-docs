# Sharding and Cross-Shard Commitment

**Status:** Partially implemented — sharded authority, cross-shard root, and discovery are live; a second independent witness and managed-hosting shards in production are not

Settlement authority can be split per integrator instead of resting with one operator. Each shard is an independent log with its own single legitimate signer, and any node can compute one cross-shard root over all known shards from public data, with no aggregator role that could become a new point of failure.

This page describes shard identity, write routing, the cross-shard root, and how shards are discovered. The single-log mechanics are in [settlement](../settlement.md); the topology picture is in [distributed topology](../distributed-topology.md).

## Shards

A shard is a `PostgresSettlementProvider`-style log: its own hash chain, Merkle tree, and signed tree heads, signed by that shard's own settlement key. Sharding adds a layer on top and does not change how any shard works internally, so existing single-shard proofs work unchanged.

- **Shard ids** look like `{namespace}:{owner}[/{instance}]`: `game:wow`, `app:...`, `service:...`, or a sibling like `game:wow/2`. Key and authority resolution use the owner only, so siblings are authorized by the same integrator's `shard_settlement` keys while remaining separate ledgers with separate heads. Nothing merges sibling ledgers.
- **`core` is the reserved shard** of the network's pinned core authority, the one node whose settlement key is pinned for the network. Identity, social, and guild events have no single owning integrator, so they route to `core`. The core authority is also the trust root registrar: an integrator and its shard key become known to the network through events recorded in its ledger.
- **Self-certifying shards.** A shard id of the form `node:<hash of public key>` proves itself: other nodes verify it with only the public key its tree-head response carries, so joining needs no registration ([witness cosigning](../../protocol/witness-cosigning.md)).
- **A node's ledger is its shard.** Whatever a node commits locally is the history of the shard it authors. A node that claims `core` while holding a different key would be indistinguishable from an impostor to a client pinned to the network key, so the server refuses to start in that situation (with a tolerance only for a lone local development node).

A shard id alone proves nothing, just as `network_id` alone proves nothing. Clients verify that a shard's key is authorized through the integrator's registered `shard_settlement` key ([network trust anchors](../../protocol/network-trust-anchors.md)).

## Write routing

An event's issuer id carries a namespace, and the namespace decides the shard.

| Namespace | Shard |
| --- | --- |
| `game`, `app`, `service` (an integrator acting as itself: attestations, revocations, integrator-owned schema events) | that integrator's own shard, `{namespace}:{owner}` |
| `identity` (identity, social, guild events) | the reserved `core` shard |

The outbox worker groups pending rows by shard and commits one batch per shard per tick, never mixing two shards in one batch. A shard is committed locally if this node holds that shard's signing key, and otherwise submitted to the shard's configured remote authority. A deployment with no remote authority configured has exactly one shard and behaves as a single-operator log. Routing picks which shard's authority to use; it never introduces a second writer for the same shard, so there is still nothing to referee.

Identity and social actions are not shard-locked: which shard an event commits into depends on the node handling the request, never on where the identity was created ([nodes](../nodes/README.md#identity-and-social-actions-are-not-shard-locked)).

## The cross-shard root

The cross-shard root must be independently computable by any node from public inputs.

- **Leaves** are `SHA-256(shard_id || tree_size || root_hash || signing_key_id || signature)`, one per known shard. Including the head's signature makes the root commit to which head was aggregated, so a rollback to a stale head is detectable.
- **Ordering** is a byte-wise ascending sort by `shard_id`, with no registration-order or other stateful ordering, so two nodes with the same set of heads build the same tree.
- **Hashing** reuses the RFC 6962 tree hash, one level up. Inclusion of a shard's head in the root uses the same proof code as a per-shard tree.
- **Result** is `CrossShardRoot { root_hash, shard_count, computed_at }`. It is deliberately not signed by any single party, because signing it would reintroduce the designated-aggregator chokepoint. A node publishes the root plus the list of heads it used, and anyone can recompute.
- **Head verification.** A shard's contributing head must verify against a key authorized for that shard and, where a witness list of more than one is known, carry a witness majority. A shard that fails is folded into the missing set, never included unverified.
- **Missing or stale shards.** A node tracks shards it knows exist and shards it holds a verified head for. If the second is a strict subset of the first, the root is marked `partial: true` and lists the missing ids. A partial root is not authoritative for the missing shards.

No consensus or cross-shard ordering is involved. A network with exactly one shard degenerates to a one-leaf root; the single-operator case is the one-shard special case, not a separate code path.

## The shard family head

An owner that runs several sibling shards (`game:<slug>` and `game:<slug>/<instance>`) can be verified as one family. Membership comes only from the shard id: instances of one owner form a family, and `core` and `node:<hash>` shards belong to none. The owner part alone decides which registered keys verify a head, so each member head is still verified exactly as in the cross-shard root.

- **A separate structure.** The family head is not the cross-shard root scoped to one owner. Its leaves use their own domain tag and bind the owner, so a family root never equals a network root over the same heads. Each leaf is `SHA-256(family tag || owner || shard_id || tree_size || root_hash || signing_key_id || signature)` with length-prefixed fields; an empty family has a fixed root derived from the owner.
- **Ordering and hashing** are the cross-shard root's: byte-wise ascending by `shard_id`, RFC 6962 tree hash, the same inclusion proof code.
- **Unsigned and recomputable.** A node publishes the root with the member heads it used, and anyone can recompute it from public heads.
- **Completeness is advisory.** Nothing declares which siblings exist, so the head covers the siblings a node knows about and has verified. A known sibling without a verified head makes the result `partial: true` and is listed in `missing_shard_ids`; a sibling the node has never heard of is invisible. A declared membership, such as an owner-signed record of its instances, would make completeness verifiable and is a separate decision.
- **Endpoint.** `GET /ledger/shard-family?owner=<namespace>:<slug>` is public and unauthenticated, like the cross-shard root, and returns the root, the member heads in canonical order and the partial information. `?member=<shard_id>` adds that member's inclusion proof. A malformed owner (including one with an instance, `core`, or a `node:` id) is a 400, a member without a verified head is a 404, and a family of more than 256 members is refused rather than truncated, because a truncated root could not be recomputed by others.

Atomic writes across siblings are out of scope; each sibling stays a single-signer log.

## Automatic shard discovery

At scale, hand-listing shards is itself a gap. Discovery uses two layers of gossip over a node's existing bounded peer connections, deliberately not a registry or directory node type.

1. A node's active announce set grows past its bootstrap list through peers discovered in announce responses ([peering](../nodes/discovery-and-peering.md)).
2. Shard-existence gossip rides on the same announce exchange: each announce carries a snapshot of the shards the sender knows and a URL claiming to serve each. A node that has real, signed history for a shard records its own claim every tick.

Discovery never implies trust. A discovered shard's head goes through the same key resolution and verification as a configured one, and an unverifiable or unreachable shard is a missing shard. Static configuration of known shards remains valid and wins on overlap.

Auto-mirroring discovered shards is a separate opt-in, since mirroring many shards' full history is a real cost. Self-certifying shards are cheap for anyone to create, so auto-mirroring them is bounded (shard counts, per-source and per-tick limits, entry size and count, backfill budget, idle eviction), and their entries stay in mirror tables and are never projected into the indexer.

## Managed hosting

An integrator without its own infrastructure can have a host run the storage, batching, and Merkle work for its shard while keeping its signing key. See [managed shard hosting](../self-hosting/managed-shard-hosting.md). The mechanism is implemented and tested. Planned: a live managed shard operated for a real integrator; none exists today.

## What is proven and what is not

Two independent shard authorities run on physically separate machines, with the primary computing a non-partial two-shard root and the second node also mirroring `core`. Two nodes given the same set of shards compute byte-identical roots. Not yet proven live: a second independent witness computing the same root. The "no privileged aggregator" property is a design invariant of the recipe, and it is not yet demonstrated by two independent computers agreeing in production.

## Implementation

Status: Partially implemented, as above. The aggregation math, routing, discovery, and the network-facing root endpoint are in the [settlement crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/chain) and [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol. Guidance for hosters choosing a shard is in the [avalon-protocol docs](https://github.com/avalon-initiative/avalon-protocol/tree/main/docs).

## Related

- [Settlement](../settlement.md)
- [Distributed topology](../distributed-topology.md)
- [Nodes](../nodes/README.md)
- [Self-hosting](../self-hosting.md)
- [Network trust anchors](../../protocol/network-trust-anchors.md), [witness cosigning](../../protocol/witness-cosigning.md)
