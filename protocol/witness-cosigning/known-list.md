# Witness Known List

**Status:** Implemented

Every node and every SDK client keeps its own bounded list of witnesses it trusts to cosign tree heads. There is no global list anyone maintains, which is part of what makes eclipse attacks impractical: an attacker facing one victim's list gains nothing against anyone else's. This page describes how the list is seeded, kept diverse, refreshed, and recovered. It is part of [witness cosigning](../witness-cosigning.md).

## Structure

- **2 anchor slots** (of a default capacity of 5), seeded from the trust-anchor list's `seed_nodes`, which are operator-diverse, pull-request-reviewed, and long-lived by convention. They exist so a freshly booted node or SDK does not compute its first-ever majority entirely from whoever it happened to discover first. An anchor's cosignature does not count for more than anyone else's, and anchors are not permanent: one going offline is handled by ordinary refill.
- **The remaining slots self-fill** from discovery, capped at 2 per diversity prefix (an IPv4 /24, an IPv6 prefix, or an operator id). The cap includes the anchor slots, so one operator cannot buy outsized influence by also running the bundled anchors. A test proves the cap holds under an arbitrarily large flood of same-prefix candidates.
- **Persisted across restarts**, so a node does not rebuild its list from scratch on every boot and hand a well-timed attacker a fresh chance to eclipse it.
- **Refill after loss.** When a slot's occupant goes stale or is removed, the freed slot is refilled from fresh discovery under the same diversity rule. The threshold recomputes at every size with no special-cased path for "the list just changed size".
- **Tenure and probation.** The production list prefers longer-tenured candidates and holds a brand-new candidate on probation (30 minutes by default) before it counts toward a majority. Both raise the cost of a burst Sybil flood timed right before an attack without changing the core rule.

## Who becomes a candidate

A node that cosigns advertises a witness advert (`key_id`, `announced_at`, `proof`) in its announce requests and responses. `key_id` is the hex verifying key, and `proof` is that key's signature over `(base_url, key_id, announced_at)` under the domain tag `avalon-witness-announce-v1`, accepted only within an hour of the verifier's clock. Slots are keyed by the cosigning key and never by network address.

A proof shows only that the key holder bound the key to that URL, not that the URL's operator agrees. An attacker could otherwise gossip an innocent host's URL bound to its own key and inherit that host's diversity prefix. So only a **direct** advert makes a candidate: one verified from the announce response received from that exact base URL, meaning the URL's own endpoint vouches for the key. Adverts learned through inbound announces or gossip are never candidates and never displace a direct advert. A node with no outbound bootstrap peers (for example a seed that only receives announces) still vouches for inbound-only peers because its announce worker also contacts a few table peers each tick that hold only a non-direct advert. Bundled anchors get their key from their own announce under the seed URL; an anchor with no proven key yet is not a candidate.

## Freshness

The window is 10 minutes by default and is scaled by how many failures the list can still absorb. With n confirmed slots, `tolerance(n) = n - majority_threshold(n)` and the effective window is `freshness_window * max(floor, tolerance(n) / tolerance(capacity))`, with a floor of 0.4. At capacity 5 that is the full 10 minutes with 5 confirmed slots, 5 minutes with 3 or 4, and 4 minutes with 2, twice the 2-minute refill interval. With zero or one confirmed slot the window is unchanged, and probationary slots always use the base window. The window is computed once per prune pass from the pre-eviction count, so a pass never tightens as it evicts. A small list drops a silent member sooner, and a fast drop can leave it at one confirmed witness, the plain author-signature case, until a probationary slot clears probation.

A witness whose most recent `observed_at` for a network's current head is older than the window is a stale slot, eligible for replacement. The same window is the age limit a verifier applies to cosignatures when accepting a head, so freshness is one rule: it applies to head acceptance, and witnesses keep their attestations fresh.

### Re-attestation

Every witness re-signs, on an interval of a third of the freshness window, its cosignature over the last head it cosigned for each log, with a new `observed_at`. It never signs a different root at that size and skips any shard with a recorded equivocation. The refreshed signature replaces the stored one and is served by `GET /ledger/sth/{n}?witnesses=1`. Without this, a head with no writes for longer than the window would stop verifying for clients that require a majority.

## Recovery when an entire list is captured or lost

This is a rare, human-noticed event, and automated recovery should not paper over it. If a node or client's whole known list goes unreachable past the freshness window, or a confirmed equivocation is found among what looked like a healthy majority, it falls back to bootstrapping a fresh list from the anchors and seed nodes the currently installed software ships with, exactly like a first boot. Recovering to a different anchor set, because the old one is known bad, is an ordinary pull-request-reviewed update to the trust-anchor list shipped in a normal release. It deliberately does not auto-trust whoever answers first after a loss.

## Implementation

Status: implemented. The pure selection logic is in [`known_list.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/known_list.rs) and the production management (persistence, peer-table discovery, probation, tenure-weighted refill) in [`crates/server/src/known_list.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/known_list.rs). The cross-language behavior is fixed by [`known-list-selection.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/conformance/vectors/known-list-selection.json) and [`witness-announce.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/conformance/vectors/witness-announce.json). Capacity, anchor count, prefix cap, freshness, and probation are hoster-configurable through `AVALON_KNOWN_LIST_*` settings.

## Related

- [Witness cosigning](../witness-cosigning.md), [gossip, evidence, and mirrors](./gossip-and-evidence.md)
- [Network trust anchors](../network-trust-anchors.md), [nodes](../../architecture/nodes/README.md), [discovery and peering](../../architecture/nodes/discovery-and-peering.md)
