# Witness Cosigning

**Status:** Partially implemented — nodes cosign, gossip, and verify by majority, and all three SDKs verify cosigned heads; the Hub does not, and the trust-anchor entry carries no witness policy.

Witness cosigning replaces "trust one settlement key" with "trust that a majority of a bounded, self-filling list of independent witnesses checked this head and found no conflicting one". Independent nodes cosign Signed Tree Heads (STHs) they have verified for append-only growth, each verifier keeps its own known list of witnesses, and two conflicting majority-cosigned heads drawn from one list must share a witness, which is proof of equivocation from signatures alone. The decision is recorded in [issue 945](https://github.com/avalon-initiative/avalon-protocol/issues/945) (core trust is witness cosigning, not a validator committee) and [issue 929](https://github.com/avalon-initiative/avalon-protocol/issues/929) (shard identity is self-certifying), consistent with [ADR 0186](../architecture/decisions/0186-no-blockchain-validator-consensus-transparency-log-only.md).

**The goal, stated once so every parameter can be checked against it:** no node, key, or operator is required for the network to keep operating or for a client to keep verifying it, including the original node. A network of one behaves under the same rule as a network of ten thousand; nothing is special-cased for small or large N.

This page covers the design and parameters. The known list is in [known list](./witness-cosigning/known-list.md); gossip, evidence, and the mirror-side flows are in [gossip, evidence, and mirrors](./witness-cosigning/gossip-and-evidence.md).

## Why this replaces the single pinned key

Originally one Ed25519 key, the settlement operator's, signed every STH and every client pinned it. That key, and whoever holds it, is a single point of trust and availability: if it is lost, compromised, or its operator disappears, nothing can be verified or extended in its name. Witness cosigning does the same head-verification job through whoever happens to be running a node, with no membership vote, token, or committee. The pinned key remains the log's own author signature and is unchanged (see [network trust anchors](./network-trust-anchors.md)); cosigning is additive and needs no reset.

## Cosignature format

A witness cosignature is a second, independent signature over the same `(tree_size, root_hash, network_id, created_at)` an author's STH signs. The author does not change how it signs; witnesses add a layer. A domain tag (`avalon-witness-cosign-v1`) ensures a cosignature can never be confused with an author's signature even though the fields overlap. Fields: the four bound values tie it to one STH, `witness_key_id` identifies the witness (the known list is keyed by key, never by network address, since an address can be spoofed or change), and `observed_at` is the witness's own timestamp, used for freshness. A cosignature attests to the head it names and never becomes false, but a verifier counts only cosignatures observed within the freshness window, so witnesses re-attest their current head on an interval.

**What a witness checks before cosigning** (the security work; the signature only publishes the result):

1. The STH's author signature verifies against the shard's currently authorized key (self-certifying, or resolved through the core registry; see [shard identity](./network-trust-anchors/shard-identity-and-names.md)).
2. A consistency proof from the last `(tree_size, root_hash)` this witness itself cosigned for that network and shard to the new one, proving an append-only extension and not a rewrite.
3. This witness has not already cosigned a different root at this exact `tree_size`.

## Default parameters

| Parameter | Default | Reason |
| --- | --- | --- |
| Known-list capacity (Y) | 5, hard cap, configurable | Bounded verification cost regardless of network size. At 5 the required count is 3, tolerating 2 failures. |
| Cosigning threshold (X) | strict majority of the actual list size: `Y_actual / 2 + 1` | Recomputed against the list's current size. At 1 (a lone node) X is 1: self-attestation, the same rule degenerating to today's single-signer case. |
| Freshness window | 10 minutes, scaled down for small confirmed lists (floor 0.4) | Age limit a verifier applies to cosignatures, and the slot-health trigger. Witnesses re-attest every third of the window. |
| Anchor slots | 2 of 5 | Reserved for bundled seed anchors; never filled by ordinary refill. |
| Diversity cap | 2 slots per prefix | Applies to every slot, anchors included. |
| Head-gossip cap | at most 5 head summaries per exchange | Small, bounded payload, not full cosignature bytes. |

**Why the threshold is a strict majority and not a fixed number.** This is the entire fork-detection guarantee, and it holds only if X is always strictly more than half of whatever list size is in play. Any two majority-sized subsets of one list share a member (checked by direct arithmetic for every size from 1 to 10,000, and by exhaustive or random subset enumeration for small lists). So two different heads at one `tree_size`, each majority-cosigned, can both exist only if some single witness cosigned both, which either did not happen (no fork) or broke rule 3 above and is now provable from the two cosignature sets. This is what makes an equivocation provable and not just unlikely.

**The author counts as the witness that holds its key.** A head's own author signature already proves that key vouches for it, so a known witness whose key is the author's is credited without a separate cosignature (the author signature is still verified first). Without this, a known list containing the shard's own author, which happens whenever an author also announces a witness key and holds a slot, could never reach a majority for that shard, since an author never cosigns its own log. The rule is part of the cosigned-head conformance vectors.

**The guarantee holds for one known list only.** Two nodes with different lists can produce two majority-cosigned heads with no shared witness, which proves nothing about any witness. What still proves misbehavior is the author's own signature: two heads at one `tree_size` with different roots, both signed by the same resolvable author key, show the author signed two roots with no cosignature needed. See [gossip, evidence, and mirrors](./witness-cosigning/gossip-and-evidence.md#author-level-evidence).

## Network sizes from one node upward

There is exactly one rule, `X = majority_threshold(current known-list size)`, evaluated identically at every size. At size 1 a node is its own sole witness. As peers are discovered the list grows toward the cap and X is recomputed at each change. The original node's departure looks like any other witness leaving a list, handled by ordinary refill.

## What is and is not in place

Implemented:

- Cosigned tree-head verification, degenerating to the plain author-signature check at a known-list size of 0 or 1, with storage and a read path (`GET /ledger/sth/latest` and `/ledger/sth/{tree_size}` accept `?witnesses=1` to return cosignatures alongside the head; the default response is unchanged, which keeps older clients working).
- Production known-list management, head-summary gossip, the cosigning decision, equivocation confirmation and evidence, and mirror-side gathering and refresh of cosignatures.
- Cosigned verification and known-list building in the Rust, C#, and TypeScript SDKs, checked by shared conformance vectors (`witness-cosigned-tree-head.json`, `known-list-selection.json`, `witness-announce.json`).
- Self-certifying `node:` shards are cosigned like any other shard.
- Per-identity chains, once listed here as unwired, are now wired in the server; see [event chains](./identity/event-chains.md).

Not done:

- **The Hub does not verify cosignatures.** It checks the author signature against the pinned key through the SDK's default path.
- **No witness policy in the trust-anchor entry.** The list is unchanged: same pinned key, same seed nodes. Whether an entry should carry witness keys or a client policy is undecided.
- **Resistance, not proof.** An attacker who controls most of a victim's known witnesses can still mislead that victim. The diversity cap, probation, anchors, and the vouch requirement raise the cost and do not remove it.

A network can move onto witness cosigning without a reset and back off again; the procedure and a live-fleet drill are maintainer runbooks in the protocol repository, tracked under [epic 942](https://github.com/avalon-initiative/avalon-protocol/issues/942).

## Implementation

Status: partially implemented.

- Pure logic: [`witness.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/witness.rs) (cosignature format, threshold), [`known_list.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/known_list.rs), [`cosigned_sth.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/cosigned_sth.rs) (`verify_cosigned_tree_head`, `find_equivocating_witnesses`).
- Server: [`witness_cosign.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/witness_cosign.rs), [`known_list.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/known_list.rs), [`cosign_verify.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/cosign_verify.rs), [`cosign_gather.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/cosign_gather.rs), [`witness_refresh.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/witness_refresh.rs), [`equivocation.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/equivocation.rs).
- Vectors: [`witness-cosigned-tree-head.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/conformance/vectors/witness-cosigned-tree-head.json), [`known-list-selection.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/conformance/vectors/known-list-selection.json), [`witness-announce.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/conformance/vectors/witness-announce.json).
- Hoster configuration (`AVALON_WITNESS_*`, `AVALON_KNOWN_LIST_*`) is documented with the server.

## Related

- [Known list](./witness-cosigning/known-list.md), [gossip, evidence, and mirrors](./witness-cosigning/gossip-and-evidence.md)
- [Network trust anchors](./network-trust-anchors.md), [shard identity](./network-trust-anchors/shard-identity-and-names.md), [trust model](./trust-model.md)
- [Settlement](../architecture/settlement.md), [mirroring](../architecture/settlement/mirroring.md), [synchronization](../architecture/synchronization.md)
