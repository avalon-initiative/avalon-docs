# Witness Gossip, Equivocation Evidence, and Mirrors

**Status:** Implemented

Fork detection in Avalon is a side effect of gossiping small head summaries, and proof of a fork is stored as evidence that anyone can re-verify from signatures alone. This page describes head gossip, how a conflict is confirmed and recorded, the decision a node makes before cosigning, and how mirrors gather and refresh other witnesses' cosignatures. It is part of [witness cosigning](../witness-cosigning.md).

## Head gossip

Nodes gossip a bounded list (at most 5 per exchange) of `(network_id/shard_id, tree_size, root_hash, cosignature_count)` summaries alongside the existing peer-gossip exchange (`POST /nodes/announce`). Summaries are validated for shape before being relayed and are never folded into the peer or shard tables. Full cosignature sets are not pushed proactively. A node that wants the full set for a summary it has seen fetches it (`GET /ledger/sth/latest?witnesses=1`).

**Fork detection is a side effect of this gossip, not a separate mechanism.** Any node or client that observes two different cosigned heads at the same `tree_size` for the same network and shard has proof of an author equivocation, and of a witness equivocation too when the two cosignature sets share a witness (the majority-intersection guarantee, valid within one known list). That is a loud, logged "stop and do not trust either head" event and is never silently auto-resolved.

## Confirming and recording a conflict

A conflicting pair of gossiped summaries is confirmed by fetching full cosignature detail from both reporting peers. The confirmation builds its known list directly from the witness keys present in the two heads, so the resulting proof is independently checkable from signatures alone and does not depend on any node's own trusted list. Each side is also topped up with cosignatures fetched from the confirmed known-list witnesses, so a bare author that serves none can still be shown to carry a majority.

### Author-level evidence

There are two kinds of evidence. If the two heads share a verifying witness, the row is stored as `witness` evidence naming it. Otherwise, if both author signatures verify under an author key this node can resolve (the pinned core key or the shard's registered `shard_settlement` keys) and the roots differ at the same network and `tree_size`, the row is stored as `author` evidence with an empty witness list. Either kind marks the shard equivocating, and a node then refuses to cosign it. The stored row holds both full heads' signed fields and both cosignature sets, so anyone can re-verify it from the row alone. This is separate from the broader source-based findings table that records any two peers disagreeing, cosigning or not.

**What remains unprovable.** Two majority-cosigned heads with different lists and no shared witness say nothing about any witness; only the author's double-signing is proven, and only when this node can resolve the author key. A node that cannot resolve the author key records nothing. A fork shown to one observer and never gossiped is not detected by anyone else. Evidence proves the author signed two roots, not which one is the honest history.

## The cosigning decision

A head reaches the cosigning decision as soon as its author signature verifies, without waiting for a majority. The decision refuses first if the shard is marked equivocating, then compares the head against this node's own last-cosigned checkpoint for that network and shard:

- no checkpoint: cosign unconditionally (bootstrap);
- same size and root: no-op;
- same size, different root: refused (no double cosign);
- smaller size: refused as stale;
- larger size: requires an RFC 6962 consistency proof, fetched from the peer that served the head and verified locally against the checkpoint root and the head root.

The checkpoint advances before the cosignature is signed and stored, so a crash between the two withholds a cosignature (repaired the next time the head is seen) and can never leave a cosignature without a checkpoint. The witness key is a dedicated witness signing key, falling back to the settlement signing key (the cosignature's own domain tag keeps one key safe across both uses). A node can opt out of cosigning; a node with no usable key never cosigns. Majority decides only whether this node then trusts and stores the head.

## Mirrors gather and refresh cosignatures

An author node serves no cosignatures of its own, so a mirror with a known list of more than one witness gathers them itself: the cosignatures attached to the source's response, plus, for each confirmed known-list witness, a request to that witness's own node. A witness's base URL is the peer-table entry whose direct advert carries its key. Fetches go through the outbound address policy, time out after 5 seconds, run at most 8 at a time, and read at most 64 KiB. A response counts only if its root, size, network, and creation time equal the head's, and each cosignature must still verify against the known-list key. If a majority is reached the head is stored and trusted with the gathered cosignatures stored for re-serving; otherwise it is held and retried next tick. A known list of 0 or 1 keeps the plain author-signature path. A mirror that has cosigned a head but not yet backfilled it serves that observed head with its cosignature, so witnesses can serve each other before any has backfilled.

**A witness speaks only for itself, and copies refresh every tick.** A gathered response counts only for the cosignature made by the witness that was asked, since relayed copies of other witnesses' cosignatures may be stale and would displace the fresh one. Every mirror-watcher tick asks each known-list witness for its own current cosignature over the latest observed head of each watched shard, whether or not the head changed and whether or not its source answered, so with the author down each mirror's copies of the other witnesses' cosignatures stay well inside the freshness window. Store rules: the same root and author timestamp with a later `observed_at` refreshes in place, an older one never replaces a newer one, and a different root is refused as a possible equivocation. A cosignature is stored only if its `observed_at` is within the freshness window before now and at most 60 seconds after it (clock skew), since a far-future timestamp would otherwise pin the stored row.

**Witnesses outside the known list are refreshed too.** A client builds its own known list, so it can include a witness a given mirror does not hold, and that witness's copy on the mirror would otherwise age out. After the known-list pass, each tick also asks a bounded selection of witnesses from the node's peer directory for their own cosignature over the same head. Only direct adverts count, one key at several URLs is one candidate, and a per-shard per-tick limit applies (16 by default, with 0 turning it off; it changes how much a node fetches and stores, never what a client accepts). Witnesses already holding a stored cosignature are asked first, stalest first. Others are admitted only while the cap has room, preferring witnesses that delivered before and then those asked longest ago, with a per-node random salt and deliberately not announcement recency, so a participant re-announcing under many proven keys cannot take every new slot. Transport failures put a witness in an in-memory backoff (30 seconds doubling to 30 minutes), while a witness that answers with nothing usable for one shard is retried for that shard after a flat 30 seconds. Every stored cosignature is served with its own `observed_at`; stale copies are kept and served, because a client applies the freshness window itself and older heads keep the cosignatures that back consistency and equivocation evidence.

## Self-certifying shards

A `node:<hash>` shard is cosigned like any other. Tree-head responses for it carry an optional `signing_public_key` outside the signed bytes. A node that mirrors discovered shards checks the key hashes to the id, signed the head, and that the head is for its own network, pins it once accepted, mirrors the log, and runs the same cosigning decision. A mirror re-serves the pinned key with the heads it serves, so a further mirror needs nothing from the author. See [shard identity](../network-trust-anchors/shard-identity-and-names.md#self-certifying-shard-ids).

## Implementation

Status: implemented. Head-summary gossip and conflict confirmation are in [`nodes.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/nodes.rs) and [`equivocation.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/equivocation.rs); the cosigning decision in [`witness_cosign.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/witness_cosign.rs); gathering and refresh in [`cosign_gather.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/cosign_gather.rs) and [`witness_refresh.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/witness_refresh.rs); storage and evidence tables in the chain crate ([`mirror.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/chain/src/mirror.rs) and [`postgres.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/chain/src/postgres.rs)).

## Related

- [Witness cosigning](../witness-cosigning.md), [known list](./known-list.md)
- [Mirroring](../../architecture/settlement/mirroring.md), [discovery and peering](../../architecture/nodes/discovery-and-peering.md), [safety limits](../../architecture/nodes/safety-limits.md)
- [Network trust anchors](../network-trust-anchors.md)
