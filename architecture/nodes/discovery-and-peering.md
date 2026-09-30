# Discovery and Peering

**Status:** Partially implemented — server-side peering, latency, and coordinates are live; capability-aware SDK routing is not built

A developer should not need to know a database address or a node hostname. SDKs resolve a node from a target network, and nodes find each other through a bounded, gossip-populated peer table. This page covers both, the measurements nodes keep about their neighbors, and how the DHT and push sync build on the peer table.

## SDK-side discovery

Every official SDK (Rust, C#, TypeScript) resolves a node itself, given a target network rather than a URL. Candidates come from the published trust-anchor list for the matching `network_id` (its server URL and seed nodes); there is no separate discovery registry, since that list is already a published node list. Each candidate is verified the same way a known URL is (its latest signed tree head is checked against the entry's pinned verify key), and the SDK picks the verified candidate with the lowest measured `GET /nodes/status` round trip. Verification always comes first; latency only orders candidates that already passed it.

Not built: ranking by geography, health, role, or operator preference. Self-hosting remains possible without any registry: a direct server URL is still accepted for local development and private deployments.

`GET /nodes/discover` is the server-side expansion endpoint: given one node, it returns that node's own status plus its full peer table in one response. SDK known-list logic uses it to find witnesses (a peer's witness advertisement is admitted only with a verifying proof), while ordinary connection selection still walks the trust-anchor list one candidate at a time. There is no capability-aware routing of individual calls by role: the peer table is a server-to-server mechanism.

## Node-to-node announce and the peer table

`POST /nodes/announce` and `GET /nodes/peers` maintain a lightweight in-memory peer table (`network_id`, roles, protocol version, last-announced time, peer-network identity and dialable addresses), keyed by base URL and never merged across `network_id`s.

- **Bootstrap.** A node announces to explicitly configured bootstrap peers; unset, it falls back to the network's seed nodes in the trust-anchor list. An empty seed list is the expected state for a network's first node, not an error.
- **Growth.** A node keeps its own active announce set, seeded from bootstrap peers (never evicted) and extended with peers discovered through announce exchanges, capped at a configurable size (default 50). A peer discovered through a bootstrap peer becomes an announce target itself, so propagation continues past one hop. A peer that stops re-announcing is dropped from both the table and the active set, freeing a slot.
- **Shard gossip.** Announce requests and responses also carry a snapshot of known shards; see [sharding](../settlement/sharding.md).
- **Admission is bounded and validated.** The peer table is filled by unauthenticated input and gossip, so admission is capped and checked ([safety limits](safety-limits.md)): a size cap with oldest-first eviction that never evicts active or bootstrap peers, address validation under the outbound address policy, a reachability check before a new entry is admitted, and a per-source limit on new peers. Gossip never writes directly into the main table: a relayed entry lands in a separate, small unverified pool and is promoted only when it announces itself or this node successfully contacts it. A hostile neighbor relaying fabricated entries can occupy the unverified pool but cannot evict a real peer.
- **The responder's own entry.** An announce response also carries the responder's own peer entry: its libp2p peer id, its advertised addresses, and a self-reported `connectivity` hint. A caller that only knew an HTTP seed learns from it how to reach the seed over libp2p, which is what lets a node behind a NAT get AutoNAT probes and a relay reservation. The caller keeps the entry only if it names the URL that was called, is on the same network and supports the protocol version, and stores it through the bounded table path, so a response can write no entry but its own.
- **Every libp2p address is validated.** Addresses in announces, gossip, and responder entries are checked before they are stored: ip4 or ip6 with tcp only, every IP through the outbound address policy (including the relay part of a relayed address), a trailing peer id equal to the announced one, one well-formed circuit at most, and bounded length and count. A forged peer id or a private address never reaches the dialer.
- **Peers with no reachable URL are confirmed over libp2p.** A gossiped peer that cannot be fetched over HTTP, which is every relayed node, waits in the unverified pool. The DHT dials a few pool entries per scan and promotes one when an outbound connection authenticates its peer id. Direct addresses are dialed before relayed ones, and of two nodes that are reachable only through a relay the one with the lower peer id dials first, so they do not open crossed relayed connections.
- **Witness advertisements.** Peer entries can carry an optional witness key advertisement with a proof of possession over `(base_url, key_id, announced_at)`. An invalid or stale one is dropped without refusing the peer ([witness cosigning](../../protocol/witness-cosigning.md)).

## Measured latency

Each announce a node sends to an active peer is timed and folded into in-memory rolling statistics keyed by peer: last, exponentially weighted, and minimum round trip, jitter (mean absolute deviation) over the last 20 successful samples, sample count, loss over the last 20 attempts, and last success time. The value is an application-level round trip (network plus the peer's request handling), not an ICMP measurement. A failed or timed-out attempt counts toward loss and never toward latency. The measurement describes one observer's path to one peer, so it is never gossiped and a peer cannot report its own latency. It is observational only and never influences admission, pruning, the version floor, or any trust decision. Nothing is persisted.

## Network coordinates

Each node holds one Vivaldi coordinate with a height term: a 3-dimensional vector in milliseconds, a height (access-link latency), and an error estimate. The estimated round trip between two nodes is the Euclidean distance between vectors plus both heights, so any two nodes can be compared without measuring the pair. Every announce carries the sender's own coordinate (an announce without one is rejected). A node publishes only its own coordinate; an observer updates its own position from its measured round trip to a neighbor and that neighbor's self-reported coordinate, and never gossips a coordinate for anyone else. A received coordinate with non-finite or out-of-range values is ignored for the update and counted. Coordinates are advisory: they never feed admission, pruning, trust, or version handling, and per-observer measured round trips remain the ground truth. Loopback deployments have near-zero round trips, so their coordinates carry no geographic meaning.

## DHT and interest lookup

The realtime relay reads each peer's roles from the peer table to decide who a live event is forwarded to. A distributed hash table (libp2p Kademlia, on by default) gives each node a peer-network identity, a fourth key domain beside player keys, issuer keys, and the settlement operator's key. It bootstraps from the same peer table rather than a second discovery mechanism. Its protocol id is namespaced by `network_id`, so a peer on another network cannot negotiate with this swarm.

Realtime relay targeting through the DHT is described in [distributed topology](../distributed-topology.md). The same mechanism records an identity locator: a background worker registers this node's locally known identities, and `GET /identities/{id}/locations` (unauthenticated, because it must work before cross-node login completes) resolves the full known set of nodes holding an identity's signing keys, never a single winner ([cross-node login](cross-node-login.md)).

## Push-assisted mirror sync

Mirrors register interest per verified network through the DHT, and an authority posts a small wake-up notification after committing a batch. It only wakes the mirror watcher early; polling remains the baseline. See [mirroring](../settlement/mirroring.md).

## Realtime relay

`POST /nodes/relay` is the one-hop receiving end of a live realtime relay. It requires no authentication (the same posture as the peer list), is single-hop by construction (the handler never forwards), and only ever feeds the receiving node's local fan-out, never its tables. The single-hop reasoning depends on a small, fully interconnected peer mesh; the DHT interest lookup is what narrows targeting as the mesh grows ([distributed topology](../distributed-topology.md)).

## Implementation

Status: Partially implemented, as above. Announce, the peer table, admission, latency, coordinates, the DHT, and the identity locator are in the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol. The trust-anchor list that supplies seed nodes is [`docs/trusted-networks.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/trusted-networks.json).

## Related

- [Nodes](README.md)
- [Connectivity](connectivity.md), [topology and tracing](topology-and-tracing.md), [safety limits](safety-limits.md)
- [Distributed topology](../distributed-topology.md)
- [SDK design](../../sdk/design.md)
- [Network trust anchors](../../protocol/network-trust-anchors.md)
